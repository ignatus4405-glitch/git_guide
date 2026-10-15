#!/usr/bin/env python3
"""Проверка курса: контент, метаданные, ссылки, собранный сайт.

Запуск::

    python3 tools/validate.py               # проверки контента (job validate)
    python3 tools/validate.py --site site   # + проверка ссылок в собранном сайте
    python3 tools/validate.py --strict      # предупреждения считать ошибками

Что проверяется:

* метаданные модулей (``content/modules.yml``) и наличие объявленных каталогов;
* front matter уроков и страниц: обязательные поля, формат даты, непустые цели/теги;
* уникальность slug-ов и URL (иначе внутренние ссылки ``lesson:`` станут неоднозначными);
* размер уроков (слишком короткий урок — ошибка, «тонкий» — предупреждение);
* сбалансированность блоков ``:::`` и ``` ``` и корректность квизов (ровно один верный ответ);
* существование файлов картинок и SVG-схем, на которые ссылается контент;
* существование целей ссылок ``lesson:``, ``page:``, ``module:``;
* отсутствие маркеров незавершённой работы (TODO, FIXME, Lorem ipsum, «заглушка»);
* (с ``--site``) все относительные ссылки и картинки в собранном HTML ведут на существующие файлы.

Код возврата: 0 — чисто (возможны предупреждения), 1 — есть ошибки или warnings при --strict.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build import ROOT, load_config  # noqa: E402
from tools import gen_diagrams  # noqa: E402
from tools.content import Site, load_site  # noqa: E402
from tools.md import _ADMONITIONS, slugify  # noqa: E402

FORBIDDEN = [
    (re.compile(r"\bTODO\b|\bFIXME\b|\bXXX\b", re.I), "маркер незавершённой работы (TODO/FIXME/XXX)"),
    (re.compile(r"lorem ipsum", re.I), "текст-заполнитель «Lorem ipsum»"),
    (re.compile(r"заглушк", re.I), "упоминание заглушки в контенте"),
    (re.compile(r"\bTBD\b"), "маркер TBD"),
]
REQUIRED_LESSON_FIELDS = ("title", "summary", "order", "updated", "goals", "tags")
REQUIRED_PAGE_FIELDS = ("title", "summary", "order")
LINK_SCHEME_RE = re.compile(r"(?:lesson|page|module):[a-z0-9\-]+(?:#[a-z0-9\-]+)?")
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^\s)]+)")
QUIZ_RE = re.compile(r"^:::\s*(quiz|note|info|tip|success|warning|danger|exercise|goal|details|terminal|history|columns)\b", re.I)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checked = 0

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")

    def tick(self) -> None:
        self.checked += 1

    @property
    def ok(self) -> bool:
        return not self.errors

    def print(self, *, strict: bool = False) -> None:
        for message in self.warnings:
            print(f"  ⚠️  {message}")
        for message in self.errors:
            print(f"  ✖  {message}")
        print(
            f"\nПроверок: {self.checked} · ошибок: {len(self.errors)} · предупреждений: {len(self.warnings)}"
        )
        if self.ok and not self.warnings:
            print("Всё чисто ✔")
        if strict and self.warnings:
            print("Режим --strict: предупреждения считаются ошибками.")


# ------------------------------------------------------------------ контент
def validate_content(root: Path, site: Site, report: Report) -> None:
    today = date.today()

    modules_yml = root / "content" / "modules.yml"
    if not modules_yml.exists():
        report.error("content/modules.yml", "файл не найден")
    else:
        report.tick()

    ids = [module.id for module in site.modules]
    if len(ids) != len(set(ids)):
        report.error("content/modules.yml", "идентификаторы модулей повторяются")
    else:
        report.tick()

    declared_dirs = {module.dir for module in site.modules}
    for path in sorted((root / "content").iterdir()):
        if path.is_dir() and path.name not in declared_dirs and path.name != "pages":
            report.warn("content/", f"каталог {path.name}/ не объявлен в modules.yml")

    for module in site.modules:
        where = f"модуль {module.id}"
        report.tick()
        for field in ("title", "description", "icon"):
            if not module.meta.get(field):
                report.error(where, f"в modules.yml не задано поле {field}")
        if not (root / "content" / module.dir).is_dir():
            report.error(where, f"каталог content/{module.dir}/ не существует")
        if not module.lessons:
            report.error(where, "в модуле нет ни одного урока")
        if module.overview is None:
            report.warn(where, "нет content/<модуль>/index.md — обзор модуля будет сгенерирован")
        if module.quizzes == 0:
            report.warn(where, "в модуле нет ни одного вопроса для самопроверки (::: quiz)")
        orders = [lesson.order for lesson in module.lessons]
        if len(orders) != len(set(orders)):
            report.warn(where, "у нескольких уроков одинаковый order — порядок будет по имени файла")

    slugs: dict[str, str] = {}
    urls: dict[str, str] = {}
    for page in site.all_pages:
        where = page.source.relative_to(root).as_posix()
        report.tick()
        if page.slug in slugs:
            report.error(where, f"slug «{page.slug}» уже используется в {slugs[page.slug]}")
        slugs[page.slug] = where
        if page.url in urls:
            report.error(where, f"URL «{page.url}» совпадает с {urls[page.url]}")
        urls[page.url] = where

        fields = REQUIRED_LESSON_FIELDS if page.kind == "lesson" else REQUIRED_PAGE_FIELDS
        for field in fields:
            if page.meta.get(field) in (None, "", []):
                report.error(where, f"во front matter нет обязательного поля «{field}»")
        if page.kind == "lesson":
            if not page.summary:
                report.error(where, "пустое поле summary")
            elif not 40 <= len(page.summary) <= 260:
                report.warn(where, f"summary длиной {len(page.summary)} символов — комфортно 40…260")
            if len(page.goals) < 2:
                report.warn(where, "меньше двух целей урока в поле goals — ученику сложнее понять результат")
            if not page.tags:
                report.warn(where, "нет тегов — они используются в навигации и поиске")
            if page.word_count < 250:
                report.error(where, f"урок слишком короткий: {page.word_count} слов (нужно ≥ 250)")
            elif page.word_count < 400:
                report.warn(where, f"короткий урок: {page.word_count} слов — стоит углубить объяснение")
            if page.code_blocks == 0:
                report.warn(where, "в уроке нет ни одного блока кода")
            if page.quiz_count == 0:
                report.warn(where, "в уроке нет вопроса самопроверки (::: quiz)")

        updated = str(page.meta.get("updated") or "")
        if updated:
            try:
                parsed = date.fromisoformat(updated)
                if parsed > today + timedelta(days=1):
                    report.warn(where, f"дата updated в будущем: {updated}")
            except ValueError:
                report.error(where, f"updated должно быть в формате YYYY-MM-DD, получено «{updated}»")

        # ------------------------------------------------------------------ тело
        body = page.body
        if body.count("```") % 2:
            report.error(where, "непарное количество ``` — не закрыт блок кода")

        depth = 0
        quiz_open = False
        quiz_options = 0
        quiz_correct = 0
        quiz_explained = False
        quiz_number = 0
        bare_fences = 0
        fence_open = False
        for line in body.splitlines():
            if line.startswith("```"):
                if not fence_open:
                    if line[3:].strip() == "":
                        bare_fences += 1
                    fence_open = True
                else:
                    fence_open = False
                continue
            if line.lstrip().startswith(":::"):
                stripped = line.lstrip()[3:].strip()
                if stripped:
                    depth += 1
                    if not QUIZ_RE.match(line.lstrip()):
                        kind = stripped.split()[0]
                        if kind not in _ADMONITIONS:
                            report.error(where, f"неизвестный тип врезки ::: {kind}")
                    if stripped.split()[0].lower() == "quiz":
                        quiz_open = True
                        quiz_number += 1
                        quiz_options = 0
                        quiz_correct = 0
                        quiz_explained = False
                else:
                    depth -= 1
                    if quiz_open:
                        if quiz_correct != 1:
                            report.error(
                                where,
                                f"в вопросе #{quiz_number} верных вариантов {quiz_correct}, а нужен ровно один "
                                "(отмечайте его как «- (x)»)",
                            )
                        if quiz_options < 2:
                            report.error(where, f"в вопросе #{quiz_number} меньше двух вариантов ответа")
                        if not quiz_explained:
                            report.warn(where, f"у вопроса #{quiz_number} нет пояснения после вариантов")
                        quiz_open = False
                continue
            if quiz_open:
                match = re.match(r"^\s*[-*]\s+\(([xX +\-)]?)\)\s*(.*)$", line)
                if match:
                    quiz_options += 1
                    if match.group(1).lower() == "x":
                        quiz_correct += 1
                elif line.strip():
                    quiz_explained = True
        if depth != 0:
            report.error(where, f"не сходятся врезки ::: (открыто {depth} лишних)")
        if bare_fences:
            report.warn(where, f"блоков кода без указания языка: {bare_fences}")
        if quiz_number == 0 and page.kind == "lesson":
            pass  # уже отмечено выше

        # маркеры незавершённой работы
        for pattern, description in FORBIDDEN:
            found = pattern.search(body)
            if found:
                report.error(where, f"найден {description}: «{found.group(0)}»")

        # ссылки-схемы
        for target in LINK_SCHEME_RE.findall(body):
            kind, _, value = target.partition(":")
            name, _, anchor = value.partition("#")
            report.tick()
            if kind == "lesson":
                target_page = site.lesson_by_slug(name)
            elif kind == "page":
                target_page = site.page_by_slug(name)
            else:
                target_page = None
                if site.module_by_id(name) is None:
                    report.error(where, f"ссылка module:{name} ведёт в несуществующий модуль")
            if kind != "module" and target_page is None:
                report.error(where, f"ссылка {kind}:{name} ведёт в никуда")
            elif anchor and target_page is not None:
                anchors = {
                    slugify(re.sub(r"[`*_]", "", m.group(2)).strip())
                    for m in re.finditer(r"^(#{1,6})\s+(.*?)\s*$", target_page.body, re.M)
                }
                if anchor not in anchors:
                    report.warn(where, f"якорь #{anchor} не найден в {kind}:{name}")

        # картинки
        for ref in IMG_RE.findall(body):
            report.tick()
            if ref.startswith(("http://", "https://", "//")):
                continue
            clean = ref.lstrip("./").split("#")[0]
            if clean.startswith("assets/img/diagrams/"):
                name = clean.split("/")[-1]
                if name not in gen_diagrams.DIAGRAMS:
                    report.error(
                        where,
                        f"схема {name} не генерируется: добавьте функцию в tools/gen_diagrams.py "
                        "и зарегистрируйте её в DIAGRAMS",
                    )
            elif not (root / clean).exists():
                report.error(where, f"файл картинки не найден: {clean}")


# ------------------------------------------------------- собранный сайт
def validate_site(site_dir: Path, report: Report) -> None:
    if not site_dir.exists():
        report.error("site/", "каталог сборки не найден — сначала запустите python3 build.py")
        return
    for required in ("index.html", "search-index.json", "sitemap.xml", "feed.xml", "404.html", "build-info.json", ".nojekyll"):
        report.tick()
        if not (site_dir / required).exists():
            report.error("site/", f"нет обязательного файла {required}")

    href_re = re.compile(r'(?:href|src)="([^"#][^"]*)"')
    checked_files = 0
    for html_file in sorted(site_dir.rglob("*.html")):
        checked_files += 1
        text = html_file.read_text(encoding="utf-8")
        # проверяем только атрибуты вне блоков кода
        text = re.sub(r"<pre[\s\S]*?</pre>", "", text)
        for ref in href_re.findall(text):
            if ref.startswith(("http://", "https://", "//", "mailto:", "data:", "tel:")):
                continue
            report.tick()
            path = html.unescape(ref).split("?")[0].split("#")[0]
            target = (html_file.parent / path).resolve()
            if not target.exists() and not (site_dir / path.lstrip("./")).exists():
                report.error(
                    html_file.relative_to(site_dir).as_posix(),
                    f"битая ссылка: {ref}",
                )
    report.tick()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Проверка контента и собранного сайта")
    parser.add_argument("--site", default="", help="каталог собранного сайта для проверки ссылок")
    parser.add_argument("--strict", action="store_true", help="предупреждения считать ошибками")
    parser.add_argument("--quiet", action="store_true", help="печатать только итог")
    args = parser.parse_args(argv)

    config = load_config(ROOT / "site.yml")
    site = load_site(ROOT, config)
    report = Report()

    if not args.quiet:
        print(f"Проверка курса «{config['title']}» v{config['version']}")
    validate_content(ROOT, site, report)
    if args.site:
        validate_site(ROOT / args.site, report)

    report.print(strict=args.strict)
    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
