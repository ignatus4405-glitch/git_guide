#!/usr/bin/env python3
"""Самотесты сборки курса: `python3 tools/test_build.py` (CI: job «test»).

Тесты проверяют не только отдельные функции, но и весь конвейер целиком:

1. мини-YAML и front matter — разбор конфигов и метаданных уроков;
2. подсветка синтаксиса — экранирование и сохранность исходного текста;
3. Markdown — заголовки, блоки кода, таблицы, врезки, квизы, картинки;
4. модель контента — уникальные slug-и, непустые уроки, корректные ссылки;
5. полная сборка в временный каталог + проверка ссылок в готовом HTML;
6. детерминизм: две сборки подряд дают идентичные файлы (кроме времени сборки);
7. валидатор: контент в репозитории проходит проверки без ошибок.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build import ROOT, load_config, main as build_main  # noqa: E402
from tools import frontmatter, highlight, yamlmini  # noqa: E402
from tools.content import load_site  # noqa: E402
from tools.md import MarkdownRenderer, slugify  # noqa: E402
from tools.validate import Report, validate_content, validate_site  # noqa: E402


class TestYamlMini(unittest.TestCase):
    def test_nested_map(self):
        data = yamlmini.loads(
            "title: Курс\n"
            "theme:\n"
            "  accent: '#f05033'\n"
            "  accent2: '#2f81f7'\n"
            "lang: ru\n"
        )
        self.assertEqual(data["title"], "Курс")
        self.assertEqual(data["theme"]["accent"], "#f05033")
        self.assertEqual(data["theme"]["accent2"], "#2f81f7")
        self.assertEqual(data["lang"], "ru")

    def test_list_of_maps(self):
        data = yamlmini.loads(
            "modules:\n"
            "  - id: first\n"
            "    title: Первый\n"
            "    tags:\n"
            "      - a\n"
            "      - b\n"
            "  - id: second\n"
            "    title: Второй\n"
        )
        self.assertEqual([m["id"] for m in data["modules"]], ["first", "second"])
        self.assertEqual(data["modules"][0]["tags"], ["a", "b"])

    def test_inline_list_and_types(self):
        data = yamlmini.loads("tags: [git, github]\norder: 3\nflag: true\nempty: null\n")
        self.assertEqual(data["tags"], ["git", "github"])
        self.assertEqual(data["order"], 3)
        self.assertIs(data["flag"], True)
        self.assertIsNone(data["empty"])

    def test_multiline_scalar(self):
        data = yamlmini.loads("description: >-\n  Первая часть\n  вторая часть\n")
        self.assertEqual(data["description"], "Первая часть вторая часть")

    def test_comments(self):
        data = yamlmini.loads("a: 1  # комментарий\n# строка целиком\nb: два\n")
        self.assertEqual(data, {"a": 1, "b": "два"})


class TestFrontMatter(unittest.TestCase):
    def test_parse(self):
        meta, body = frontmatter.parse(
            "---\ntitle: Урок\norder: 2\ngoals:\n  - Понять\n  - Проверить\ntags: [git]\n---\nТекст урока\n"
        )
        self.assertEqual(meta["title"], "Урок")
        self.assertEqual(meta["order"], 2)
        self.assertEqual(meta["goals"], ["Понять", "Проверить"])
        self.assertEqual(meta["tags"], ["git"])
        self.assertEqual(body.strip(), "Текст урока")

    def test_without_front_matter(self):
        meta, body = frontmatter.parse("Просто текст")
        self.assertEqual(meta, {})
        self.assertEqual(body, "Просто текст")

    def test_unclosed_raises(self):
        with self.assertRaises(frontmatter.FrontMatterError):
            frontmatter.parse("---\ntitle: X\nТекст без закрывающих дефисов")


class TestHighlight(unittest.TestCase):
    def test_escapes_html(self):
        out = highlight.highlight("git log <html>", "bash")
        self.assertNotIn("<html>", out)
        self.assertIn("&lt;", out)
        self.assertNotIn("<script>", highlight.highlight("echo <script>", "bash"))

    def test_text_is_preserved(self):
        """Подсветка не теряет и не дублирует символы исходного кода."""
        import html as html_mod
        import re as re_mod

        code = 'git commit -m "fix: правка" && npm test\necho $HOME # конец'
        for lang in ("bash", "text", "yaml", "python", "json", "html"):
            out = highlight.highlight(code, lang)
            plain = html_mod.unescape(re_mod.sub(r"<[^>]+>", "", out)).replace("&#x27;", "'").replace("&quot;", '"')
            self.assertEqual(plain.strip(), code.strip(), lang)

    def test_unknown_language_is_plain(self):
        out = highlight.highlight("любой текст <b>", "не-язык")
        self.assertEqual(out, "любой текст &lt;b&gt;")


class TestMarkdown(unittest.TestCase):
    def renderer(self, resolve=None):
        return MarkdownRenderer(resolve or (lambda kind, value: f"/{kind}/{value}"))

    def test_headings_and_toc(self):
        r = self.renderer()
        out = r.render("# Заголовок\n\n## Второй раздел\n\n### Третий\n\nТекст\n")
        self.assertIn("<h1", out)
        self.assertIn('id="vtoroy-razdel"', out)
        self.assertEqual([e["id"] for e in r.toc], ["vtoroy-razdel", "tretiy"])

    def test_code_fence_with_language_and_title(self):
        out = self.renderer().render('```bash title="git log"\ngit log --oneline\n```\n')
        self.assertIn('data-lang="bash"', out)
        self.assertIn("git log", out)
        self.assertIn("Скопировать", out)

    def test_table(self):
        out = self.renderer().render("| Команда | Смысл |\n| --- | ---: |\n| `git status` | Состояние |\n")
        self.assertIn("<table>", out)
        self.assertIn('<th style="text-align:left">Команда</th>', out)
        self.assertIn('<th style="text-align:right">Смысл</th>', out)

    def test_admonitions(self):
        out = self.renderer().render("::: warning Осторожно\nТекст предупреждения\n:::\n")
        self.assertIn("adm--warning", out)
        self.assertIn("Осторожно", out)
        self.assertIn("Текст предупреждения", out)

    def test_details_admonition(self):
        out = self.renderer().render("::: details Как это работает\nСкрытый текст\n:::\n")
        self.assertIn("<details", out)
        self.assertIn("<summary", out)

    def test_quiz_marks_correct_answer(self):
        out = self.renderer().render(
            "::: quiz Вопрос?\n- ( ) Неверно\n- (x) Верно\n- ( ) Тоже неверно\n\nПояснение.\n:::\n"
        )
        self.assertEqual(out.count('data-correct="1"'), 1)
        self.assertEqual(out.count('data-correct="0"'), 2)
        self.assertIn("quiz__explain", out)

    def test_image_uses_resolver(self):
        out = self.renderer().render('![Схема](assets/img/diagrams/three-trees.svg "Подпись")\n')
        self.assertIn('<figure>', out)
        self.assertIn('src="/asset/assets/img/diagrams/three-trees.svg"', out)
        self.assertIn("<figcaption>Подпись</figcaption>", out)

    def test_internal_link_scheme(self):
        out = self.renderer().render("См. [первый урок](lesson:chto-takoe-git)\n")
        self.assertIn('href="/lesson/chto-takoe-git"', out)

    def test_lists_and_tasks(self):
        out = self.renderer().render("- [x] Сделано\n- [ ] Не сделано\n")
        self.assertIn('type="checkbox" disabled checked', out)
        self.assertIn("task-list", out)

    def test_raw_html_allowed_but_scripts_escaped(self):
        out = self.renderer().render("<kbd>Ctrl</kbd>\n\n<div>нормальный блок</div>\n")
        self.assertIn("<kbd>Ctrl</kbd>", out)
        evil = self.renderer().render('<img src=x onerror="alert(1)">\n')
        self.assertNotIn("onerror=\"alert", evil)

    def test_nested_list(self):
        out = self.renderer().render("- первый\n  - вложенный\n- второй\n")
        self.assertEqual(out.count("<ul>"), 2)

    def test_slugify_cyrillic(self):
        self.assertEqual(slugify("Три «дерева» Git"), "tri-dereva-git")


class TestContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config(ROOT / "site.yml")
        cls.site = load_site(ROOT, cls.config)

    def test_modules_loaded(self):
        self.assertGreaterEqual(len(self.site.modules), 5)
        for module in self.site.modules:
            self.assertTrue(module.lessons, f"в модуле {module.id} нет уроков")
            self.assertTrue(module.title)

    def test_unique_slugs_and_urls(self):
        slugs = [page.slug for page in self.site.all_pages]
        urls = [page.url for page in self.site.all_pages]
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertEqual(len(urls), len(set(urls)))

    def test_lessons_have_substance(self):
        for lesson in self.site.lessons:
            self.assertGreater(lesson.word_count, 250, lesson.slug)
            self.assertTrue(lesson.summary, lesson.slug)
            self.assertTrue(lesson.goals, lesson.slug)

    def test_resolver_builds_paths(self):
        lesson = self.site.lessons[0]
        self.assertTrue(lesson.url.startswith("module/"))
        self.assertEqual(self.site.resolve(lesson, "lesson", lesson.slug), "../../" + lesson.url)


class TestFullBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "site"
        cls.code = build_main(["--out", str(cls.out), "--quiet"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_build_succeeds(self):
        self.assertEqual(self.code, 0)

    def test_expected_files(self):
        for name in ("index.html", "search-index.json", "sitemap.xml", "feed.xml", "404.html", "build-info.json", ".nojekyll"):
            self.assertTrue((self.out / name).exists(), name)
        self.assertTrue((self.out / "assets" / "css" / "site.css").exists())
        self.assertTrue((self.out / "assets" / "js" / "app.js").exists())
        self.assertTrue((self.out / "assets" / "img" / "diagrams" / "three-trees.svg").exists())

    def test_every_page_rendered(self):
        site = load_site(ROOT, load_config(ROOT / "site.yml"))
        for page in site.all_pages:
            target = self.out / page.url
            self.assertTrue(target.exists(), page.url)
            text = target.read_text(encoding="utf-8")
            # главная страница показывает не свой title, а заголовок курса в hero-блоке
            expected = page.title if page.slug != "index" else site.config["title"]
            self.assertIn(expected, text, page.url)

    def test_search_index(self):
        data = json.loads((self.out / "search-index.json").read_text(encoding="utf-8"))
        site = load_site(ROOT, load_config(ROOT / "site.yml"))
        self.assertEqual(len(data["items"]), len(site.all_pages))
        self.assertTrue(all(item["u"].endswith(".html") for item in data["items"]))

    def test_percent_in_markup_is_not_broken(self):
        """Проценты в шаблонах и стилях не должны ломать форматирование страницы."""
        text = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-progress-fill style="width:0%"', text)
        self.assertIn("data-search-open", text)
        self.assertNotIn("{", text.split("<body")[0].split("<script>")[0].replace("{", "", 0) or "")

    def test_built_site_has_no_broken_links(self):
        report = Report()
        validate_site(self.out, report)
        self.assertEqual(report.errors, [])

    def test_build_is_deterministic(self):
        second = Path(self.tmp.name) / "site2"
        build_main(["--out", str(second), "--quiet"])
        for path in sorted(self.out.rglob("*")):
            if not path.is_file() or path.name == "build-info.json":
                continue
            mirror = second / path.relative_to(self.out)
            self.assertEqual(path.read_bytes(), mirror.read_bytes(), str(path))


class TestValidatorOnRepository(unittest.TestCase):
    def test_content_is_valid(self):
        config = load_config(ROOT / "site.yml")
        site = load_site(ROOT, config)
        report = Report()
        validate_content(ROOT, site, report)
        self.assertEqual(report.errors, [], "\n".join(report.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
