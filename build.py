#!/usr/bin/env python3
"""Сборка статического сайта курса «Git и GitHub» из markdown-контента.

Запуск::

    python3 build.py                     # собрать сайт в ./site
    python3 build.py --out public        # другой каталог
    python3 build.py --strict            # падать на предупреждениях
    python3 build.py --no-diagrams       # не генерировать SVG-схемы

Что делает сборка:

1. читает ``site.yml`` (метаданные сайта) и ``content/`` (модули, уроки, страницы);
2. генерирует SVG-схемы из ``tools/gen_diagrams.py`` в ``assets/img/diagrams/``;
3. рендерит каждую страницу в HTML (шаблоны — ``tools/templates.py``);
4. собирает поисковый индекс ``search-index.json``, ``sitemap.xml``, ``feed.xml``,
   ``robots.txt``, ``404.html`` и ``build-info.json``;
5. обновляет машиночитаемый манифест и журнал состояния для агентов
   (``docs/MANIFEST.json``, ``docs/STATE.md``) — см. ``tools/gen_state.py``.

Сборка идемпотентна: одинаковый вход → одинаковый выход (кроме даты сборки).
Именно эту команду запускает GitHub Actions (см. .github/workflows/ci.yml).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools import frontmatter, gen_diagrams, gen_state, templates, yamlmini  # noqa: E402
from tools.templates import plural  # noqa: E402
from tools.content import Page, Site, load_site  # noqa: E402
from tools.md import MarkdownRenderer  # noqa: E402

ROOT = Path(__file__).resolve().parent
TOKEN_RE = re.compile(r"\[\[([A-Z_]+)\]\]")


# --------------------------------------------------------------------- git
def git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False, timeout=20
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return ""


def git_revision() -> str:
    return git("rev-parse", "--short", "HEAD") or "unknown"


def git_branch() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"


def file_dates() -> dict[str, str]:
    """Дата последнего коммита для каждого файла репозитория (одним вызовом git)."""
    out = git("log", "--pretty=format:@@%cs", "--name-only", "--no-renames")
    dates: dict[str, str] = {}
    current = ""
    for line in out.split("\n"):
        if line.startswith("@@"):
            current = line[2:]
        elif line.strip() and current:
            dates.setdefault(line.strip(), current)
    return dates


# ------------------------------------------------------ вспомогательные блоки
def plain_text(md_text: str, limit: int = 2400) -> str:
    """Грубое превращение markdown в текст для поискового индекса."""
    text = re.sub(r"```[\s\S]*?```", lambda m: " " + m.group(0).strip("`\n") + " ", md_text)
    text = re.sub(r"<!--[\s\S]*?-->", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s*:::\s*", " ", text, flags=re.M)
    text = re.sub(r"[#>*`|_]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:limit]


def module_map_html(site: Site, prefix: str) -> str:
    """HTML-карта курса: используется как токен [[MODULE_MAP]] в markdown-страницах."""
    blocks = []
    for module in site.modules:
        lessons = "".join(
            f'<li><a href="{prefix}{lesson.url}">{lesson.order if lesson.order < 999 else "·"}. '
            f"{lesson.title}</a> <span class='dim'>~{lesson.reading_time} мин</span></li>"
            for lesson in module.lessons
        )
        blocks.append(
            f'<section class="map-module"><h3 id="module-{module.id}">'
            f'<span aria-hidden="true">{module.icon}</span> '
            f'<a href="{prefix}{module.url}">{module.title}</a></h3>'
            f'<p class="dim">{module.description}</p><ol class="map-lessons">{lessons}</ol></section>'
        )
    return "".join(blocks)


def stats_html(site: Site) -> str:
    stats = site.stats()
    cards = [
        (stats["modules"], plural(stats["modules"], "модуль", "модуля", "модулей")),
        (stats["lessons"], plural(stats["lessons"], "урок", "урока", "уроков")),
        (stats["quizzes"], plural(stats["quizzes"], "вопрос", "вопроса", "вопросов")),
        (f"≈{stats['minutes']}", plural(stats["minutes"], "минута", "минуты", "минут") + " чтения"),
        (stats["code_blocks"], plural(stats["code_blocks"], "блок", "блока", "блоков") + " кода"),
        (len(gen_diagrams.DIAGRAMS), plural(len(gen_diagrams.DIAGRAMS), "схема", "схемы", "схем")),
    ]
    return (
        '<ul class="stat-grid">'
        + "".join(f'<li><strong>{value}</strong><span>{label}</span></li>' for value, label in cards)
        + "</ul>"
    )


def module_cards_html(site: Site, prefix: str) -> str:
    cards = []
    for idx, module in enumerate(site.modules, start=1):
        cards.append(
            f'<a class="module-card" href="{prefix}{module.url}">'
            f'<span class="module-card__top"><span class="module-card__icon" aria-hidden="true">{module.icon}</span>'
            f'<span class="module-card__num">Модуль {idx}</span></span>'
            f'<strong class="module-card__title">{module.title}</strong>'
            f'<span class="module-card__desc">{module.description}</span>'
            f'<span class="module-card__foot">{len(module.lessons)} '
            f"{plural(len(module.lessons), 'урок', 'урока', 'уроков')} · ≈{module.minutes} мин"
            + (f" · 🧩 {module.quizzes}" if module.quizzes else "")
            + "</span></a>"
        )
    return '<div class="module-grid">' + "".join(cards) + "</div>"


def hero_html(site: Site, page: Page) -> str:
    cfg = site.config
    return f"""
<section class="hero">
  <p class="hero__eyebrow">{cfg.get('course_level', 'Курс')} · версия {cfg['version']}</p>
  <h1 class="hero__title">Git и GitHub: от первого коммита<br>до автоматизации в Actions</h1>
  <p class="hero__lead">{cfg['description']}</p>
  <div class="hero__actions">
    <a class="btn btn--primary" href="{page.prefix}{site.modules[0].lessons[0].url}">
      Начать курс → <small>{site.modules[0].lessons[0].title}</small></a>
    <a class="btn" href="{page.prefix}karta-kursa.html">Карта курса</a>
    <a class="btn btn--ghost" href="{page.prefix}shpargalka.html">Шпаргалка команд</a>
  </div>
  {stats_html(site)}
</section>
"""


# ------------------------------------------------------------------ страницы
class Builder:
    def __init__(self, site: Site, out_dir: Path, *, diagrams: bool = True, quiet: bool = False):
        self.site = site
        self.out = out_dir
        self.quiet = quiet
        self.diagrams = diagrams
        self.build_time = templates.now_utc()
        self.revision = git_revision()
        self.branch = git_branch()
        self.dates = file_dates()
        self.warnings: list[str] = []
        self.written: list[str] = []

    # -------------------------------------------------------------- утилиты
    def log(self, message: str) -> None:
        if not self.quiet:
            print(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"::warning title=Сборка::{message}")

    def write(self, rel_path: str, content: str) -> None:
        target = self.out / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.written.append(rel_path)

    def renderer_for(self, page: Page) -> MarkdownRenderer:
        site = self.site

        def resolve(kind: str, value: str) -> str:
            return site.resolve(page, kind, value)

        return MarkdownRenderer(resolve)

    def updated_of(self, page: Page) -> str:
        rel = page.source.relative_to(self.site.root).as_posix()
        git_date = self.dates.get(rel, "")
        front = str(page.meta.get("updated") or "")
        dates = [d for d in (git_date, front) if d]
        return max(dates) if dates else ""

    def materialize_tokens(self, page: Page, body: str) -> str:
        prefix = page.prefix

        def replace(match: re.Match[str]) -> str:
            token = match.group(1)
            if token == "MODULE_MAP":
                return module_map_html(self.site, prefix)
            if token == "STATS":
                return stats_html(self.site)
            if token == "MODULE_CARDS":
                return module_cards_html(self.site, prefix)
            if token == "LESSON_COUNT":
                return str(len(self.site.lessons))
            self.warn(f"{page.source.name}: неизвестный токен [[{token}]]")
            return match.group(0)

        return TOKEN_RE.sub(replace, body)

    # ------------------------------------------------------------------ вход
    def run(self) -> dict:
        self.out.mkdir(parents=True, exist_ok=True)
        self.copy_assets()
        self.render_lessons()
        self.render_pages()
        self.render_search_index()
        self.render_sitemap_and_feed()
        self.render_extras()
        self.render_build_info()
        return self.build_info()

    def copy_assets(self) -> None:
        src = ROOT / "assets"
        if src.exists():
            shutil.copytree(src, self.out / "assets", dirs_exist_ok=True)
        if self.diagrams:
            names = gen_diagrams.write_all(self.out / "assets" / "img" / "diagrams")
            self.log(f"  · схем SVG: {len(names)}")
        else:
            # даже без генерации нужны файлы, иначе ссылки в контенте сломаются
            gen_diagrams.write_all(self.out / "assets" / "img" / "diagrams")

    def render_lessons(self) -> None:
        for module in self.site.modules:
            overview = module.overview
            if overview is None:
                page = Page(
                    kind="module",
                    slug=module.id,
                    title=module.title,
                    summary=module.description,
                    body="",
                    source=ROOT / "content" / module.dir,
                    url=f"module/{module.id}/index.html",
                    module_id=module.id,
                    meta={"updated": "", "nav": False},
                )
                page.body = ""
                body_html = templates.module_overview_html(self.site, module, page)
                toc_entries: list[dict] = []
            else:
                page = overview
                renderer = self.renderer_for(page)
                body_html = renderer.render(self.materialize_tokens(page, page.body))
                toc_entries = renderer.toc
            page.meta["updated"] = self.updated_of(page) or page.meta.get("updated", "")
            self.write(
                page.url,
                templates.page_shell(
                    self.site,
                    page,
                    body_html=body_html,
                    toc_entries=toc_entries,
                    build_time=self.build_time,
                    revision=self.revision,
                ),
            )

            for lesson in module.lessons:
                lesson.meta["updated"] = self.updated_of(lesson)
                renderer = self.renderer_for(lesson)
                body = self.materialize_tokens(lesson, lesson.body)
                body_html = (
                    f"<h1>{lesson.title}</h1>"
                    + (f'<p class="lead">{lesson.summary}</p>' if lesson.summary else "")
                    + templates.lesson_meta_bar(self.site, lesson)
                    + templates.goals(self.site, lesson)
                    + renderer.render(body)
                )
                self.write(
                    lesson.url,
                    templates.page_shell(
                        self.site,
                        lesson,
                        body_html=body_html,
                        toc_entries=renderer.toc,
                        build_time=self.build_time,
                        revision=self.revision,
                    ),
                )

    def render_pages(self) -> None:
        for page in self.site.pages:
            page.meta["updated"] = self.updated_of(page)
            renderer = self.renderer_for(page)
            body = self.materialize_tokens(page, page.body)
            body_html = renderer.render(body)
            extra_top = ""
            if page.slug == "index":
                extra_top = hero_html(self.site, page) + '<p class="lead">' + page.summary + "</p>"
                body_html = module_cards_html(self.site, page.prefix) + body_html
            self.write(
                page.url,
                templates.page_shell(
                    self.site,
                    page,
                    body_html=body_html,
                    toc_entries=renderer.toc,
                    build_time=self.build_time,
                    revision=self.revision,
                    extra_top=extra_top,
                ),
            )

    def render_search_index(self) -> None:
        entries = []
        for page in self.site.all_pages:
            if page.url == "404.html":
                continue
            module = self.site.module_by_id(page.module_id) if page.module_id else None
            entries.append(
                {
                    "t": page.title,
                    "u": page.url,
                    "s": page.summary,
                    "k": page.kind,
                    "m": module.title if module else "Материалы",
                    "o": page.order if page.order < 999 else 0,
                    "x": plain_text(page.body),
                }
            )
        payload = {
            "generated": self.build_time,
            "version": self.site.config["version"],
            "items": entries,
        }
        self.write("search-index.json", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    def render_sitemap_and_feed(self) -> None:
        base = self.site.config["base_url"].rstrip("/")
        urls = []
        for page in self.site.all_pages:
            lastmod = page.meta.get("updated") or self.dates.get(
                page.source.relative_to(self.site.root).as_posix(), ""
            )
            urls.append({"loc": f"{base}/{page.url}", "lastmod": lastmod})
        urls.append({"loc": f"{base}/karta-kursa.html", "lastmod": ""})
        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(
                f"  <url><loc>{u['loc']}</loc>"
                + (f"<lastmod>{u['lastmod']}</lastmod>" if u["lastmod"] else "")
                + "</url>\n"
                for u in urls
            )
            + "</urlset>\n"
        )
        self.write("sitemap.xml", sitemap)

        items = []
        lessons = sorted(
            self.site.lessons,
            key=lambda p: (p.meta.get("updated") or "1970-01-01"),
            reverse=True,
        )[:20]
        for lesson in lessons:
            date = lesson.meta.get("updated") or ""
            items.append(
                "<item>"
                f"<title>{lesson.title}</title>"
                f"<link>{base}/{lesson.url}</link>"
                f"<guid isPermaLink=\"true\">{base}/{lesson.url}</guid>"
                + (f"<pubDate>{date}T00:00:00Z</pubDate>" if date else "")
                + f"<description>{lesson.summary}</description>"
                "</item>"
            )
        feed = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0"><channel>'
            f"<title>{self.site.config['title']}</title>"
            f"<link>{base}/</link>"
            f"<description>{self.site.config['description']}</description>"
            f"<language>{self.site.config['lang']}</language>"
            + "".join(items)
            + "</channel></rss>\n"
        )
        self.write("feed.xml", feed)
        self.write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")

    def render_extras(self) -> None:
        (self.out / ".nojekyll").write_text("", encoding="utf-8")
        first = self.site.modules[0].lessons[0]
        notfound = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Страница не найдена · {self.site.config['short_title']}</title>
<link rel="stylesheet" href="assets/css/site.css"><meta name="robots" content="noindex"></head>
<body><main class="notfound">
<h1>404</h1>
<p>Такой страницы в курсе нет. Возможно, ссылка устарела после перестройки контента.</p>
<ul>
  <li><a href="index.html">Главная страница курса</a></li>
  <li><a href="karta-kursa.html">Карта курса: все модули и уроки</a></li>
  <li><a href="{first.url}">Первый урок: {first.title}</a></li>
</ul>
<p class="dim">Совет: поиск по курсу открывается клавишей «/» или Ctrl+K.</p>
</main></body></html>
"""
        self.write("404.html", notfound)

    def build_info(self) -> dict:
        stats = self.site.stats()
        return {
            "title": self.site.config["title"],
            "version": self.site.config["version"],
            "built_at": self.build_time,
            "revision": self.revision,
            "branch": self.branch,
            "stats": stats,
            "files": sorted(self.written),
            "warnings": self.warnings,
        }

    def render_build_info(self) -> None:
        info = self.build_info()
        self.write("build-info.json", json.dumps(info, ensure_ascii=False, indent=2) + "\n")
        gen_state.write(self.site, info, ROOT)


def load_config(path: Path) -> dict:
    raw = yamlmini.loads(path.read_text(encoding="utf-8")) or {}
    required = ["title", "short_title", "description", "base_url", "repo"]
    missing = [key for key in required if not raw.get(key)]
    if missing:
        raise SystemExit(f"site.yml: не заданы обязательные поля: {', '.join(missing)}")
    raw.setdefault("lang", "ru")
    raw.setdefault("version", "0.0.0")
    raw.setdefault("author", "unknown")
    raw.setdefault("license", "MIT")
    raw.setdefault("repo_branch", "main")
    raw.setdefault("theme", {})
    raw["theme"].setdefault("accent", "#f05033")
    raw["theme"].setdefault("accent2", "#2f81f7")
    raw["theme"].setdefault("accent3", "#3fb950")
    raw["theme"].setdefault("accent4", "#a371f7")
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Сборка сайта курса по Git и GitHub")
    parser.add_argument("--out", default="site", help="каталог вывода (по умолчанию site/)")
    parser.add_argument("--config", default="site.yml", help="файл конфигурации сайта")
    parser.add_argument("--strict", action="store_true", help="останавливаться на предупреждениях")
    parser.add_argument("--no-diagrams", action="store_true", help="не перегенерировать SVG-схемы")
    parser.add_argument("--quiet", action="store_true", help="меньше вывода")
    args = parser.parse_args(argv)

    config = load_config(ROOT / args.config)
    site = load_site(ROOT, config)
    builder = Builder(site, ROOT / args.out, diagrams=not args.no_diagrams, quiet=args.quiet)

    if not args.quiet:
        print(f"Сборка «{config['title']}» v{config['version']}")
        print(f"  · модулей: {len(site.modules)}, уроков: {len(site.lessons)}, страниц: {len(site.pages)}")
    info = builder.run()

    if not args.quiet:
        print(f"Готово: {len(info['files'])} файлов → {args.out}/ (ревизия {info['revision']})")
    if builder.warnings:
        print(f"Предупреждений: {len(builder.warnings)}")
        if args.strict:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
