"""Модель контента курса: модули, уроки, отдельные страницы.

Структура каталога ``content/``::

    content/
      modules.yml          # порядок и метаданные модулей
      pages/               # отдельные страницы (главная, карта курса, шпаргалка…)
        index.md
        roadmap.md
      <module-dir>/        # каталог модуля, имя задано в modules.yml
        index.md           # обзор модуля (необязателен)
        01-....md          # уроки, порядок — по полю order во front matter

Каждый markdown-файл начинается с front matter (см. tools/frontmatter.py):

    ---
    title: "Заголовки и чтение истории"
    summary: "Что попадает в git log и как читать граф коммитов."
    order: 4
    updated: 2026-10-15
    tags: [git, log]
    goals:
      - Читать однострочный лог
      - Понимать, чем git log отличается от git show
    ---

Модуль page/lesson превращается в объект :class:`Page` с готовыми URL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter, yamlmini

WORDS_PER_MINUTE = 160
FENCE_RE = re.compile(r"```[\s\S]*?```")


@dataclass
class Page:
    """Одна markdown-страница: урок, обзор модуля или отдельная страница."""

    kind: str  # "page" | "lesson" | "module"
    slug: str  # глобально уникальный идентификатор (используется в ссылках lesson:<slug>)
    title: str
    summary: str
    body: str
    source: Path
    url: str = ""
    order: int = 999
    module_id: str | None = None
    meta: dict = field(default_factory=dict)

    # ---------------------------------------------------------------- утилиты
    @property
    def tags(self) -> list[str]:
        value = self.meta.get("tags") or []
        return [str(v) for v in value] if isinstance(value, list) else [str(value)]

    @property
    def goals(self) -> list[str]:
        value = self.meta.get("goals") or []
        if isinstance(value, str):
            return [value]
        return [str(v) for v in value]

    @property
    def updated(self) -> str:
        return str(self.meta.get("updated") or "")

    @property
    def exercise(self) -> str:
        return str(self.meta.get("exercise") or "")

    @property
    def depth(self) -> int:
        return max(self.url.count("/"), 0)

    @property
    def prefix(self) -> str:
        """Префикс относительных ссылок вида ``../../``."""
        return "../" * self.depth

    @property
    def word_count(self) -> int:
        text = FENCE_RE.sub(" ", self.body)
        text = re.sub(r"[#>*`|_\-]+", " ", text)
        return len([w for w in text.split() if any(ch.isalnum() for ch in w)])

    @property
    def reading_time(self) -> int:
        return max(1, round(self.word_count / WORDS_PER_MINUTE))

    @property
    def quiz_count(self) -> int:
        return len(re.findall(r"^:::\s*quiz", self.body, flags=re.M))

    @property
    def code_blocks(self) -> int:
        return len(re.findall(r"^```", self.body, flags=re.M)) // 2


@dataclass
class Module:
    id: str
    dir: str
    title: str
    description: str
    icon: str
    level: str
    lessons: list[Page] = field(default_factory=list)
    overview: Page | None = None
    meta: dict = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"module/{self.id}/index.html"

    @property
    def words(self) -> int:
        return sum(p.word_count for p in self.lessons)

    @property
    def minutes(self) -> int:
        return sum(p.reading_time for p in self.lessons)

    @property
    def quizzes(self) -> int:
        return sum(p.quiz_count for p in self.lessons)


@dataclass
class Site:
    config: dict
    modules: list[Module]
    pages: list[Page]
    root: Path

    # ------------------------------------------------------------------ поиск
    @property
    def lessons(self) -> list[Page]:
        out: list[Page] = []
        for module in self.modules:
            out.extend(module.lessons)
        return out

    @property
    def all_pages(self) -> list[Page]:
        return [p for p in self.pages] + self.lessons

    def lesson_by_slug(self, slug: str) -> Page | None:
        for lesson in self.lessons:
            if lesson.slug == slug:
                return lesson
        return None

    def page_by_slug(self, slug: str) -> Page | None:
        for page in self.pages:
            if page.slug == slug:
                return page
        return None

    def module_by_id(self, module_id: str) -> Module | None:
        for module in self.modules:
            if module.id == module_id:
                return module
        return None

    def resolve(self, current: Page, kind: str, value: str) -> str:
        """Преобразует схемы контента (lesson:/page:/module:/asset:) в URL."""
        fragment = ""
        if "#" in value:
            value, _, fragment = value.partition("#")
            fragment = "#" + fragment
        if kind == "lesson":
            lesson = self.lesson_by_slug(value)
            target = lesson.url if lesson else f"lesson-missing/{value}.html"
        elif kind == "page":
            page = self.page_by_slug(value)
            target = page.url if page else f"page-missing/{value}.html"
        elif kind == "module":
            module = self.module_by_id(value)
            target = module.url if module else f"module/{value}/index.html"
        else:  # asset и обычные относительные пути
            target = value
        return current.prefix + target + fragment

    def neighbours(self, lesson: Page) -> tuple[Page | None, Page | None]:
        chain = self.lessons
        for idx, item in enumerate(chain):
            if item.slug == lesson.slug:
                return (chain[idx - 1] if idx else None, chain[idx + 1] if idx + 1 < len(chain) else None)
        return None, None

    def stats(self) -> dict:
        lessons = self.lessons
        return {
            "modules": len(self.modules),
            "lessons": len(lessons),
            "pages": len(self.pages),
            "words": sum(p.word_count for p in self.all_pages),
            "minutes": sum(p.reading_time for p in self.all_pages),
            "quizzes": sum(p.quiz_count for p in lessons),
            "code_blocks": sum(p.code_blocks for p in self.all_pages),
        }


def _slug_from_filename(path: Path) -> str:
    name = path.stem
    name = re.sub(r"^\d+[-_.]?", "", name)
    return name.lower()


def load_site(root: Path, config: dict) -> Site:
    """Читает content/ и собирает объект :class:`Site`."""
    content_dir = root / "content"
    pages_dir = content_dir / "pages"

    modules_raw = yamlmini.loads((content_dir / "modules.yml").read_text(encoding="utf-8")) or []
    if not isinstance(modules_raw, list):
        raise ValueError("content/modules.yml должен быть списком модулей")

    modules: list[Module] = []
    for item in modules_raw:
        module = Module(
            id=str(item["id"]),
            dir=str(item.get("dir") or item["id"]),
            title=str(item.get("title") or item["id"]),
            description=str(item.get("description") or ""),
            icon=str(item.get("icon") or "📦"),
            level=str(item.get("level") or ""),
            meta=item,
        )
        module_dir = content_dir / module.dir
        overview_path = module_dir / "index.md"
        if overview_path.exists():
            meta, body = frontmatter.parse(overview_path.read_text(encoding="utf-8"))
            module.overview = Page(
                kind="module",
                slug=module.id,
                title=str(meta.get("title") or module.title),
                summary=str(meta.get("summary") or module.description),
                body=body,
                source=overview_path,
                url=f"module/{module.id}/index.html",
                module_id=module.id,
                meta=meta,
            )
        for path in sorted(module_dir.glob("*.md")):
            if path.name == "index.md":
                continue
            meta, body = frontmatter.parse(path.read_text(encoding="utf-8"))
            order = meta.get("order")
            prefix_num = re.match(r"^(\d+)", path.stem)
            if order is None and prefix_num:
                order = int(prefix_num.group(1))
            lesson = Page(
                kind="lesson",
                slug=_slug_from_filename(path),
                title=str(meta.get("title") or path.stem),
                summary=str(meta.get("summary") or ""),
                body=body,
                source=path,
                url=f"module/{module.id}/{_slug_from_filename(path)}.html",
                order=int(order or 999),
                module_id=module.id,
                meta=meta,
            )
            module.lessons.append(lesson)
        module.lessons.sort(key=lambda p: (p.order, p.source.name))
        modules.append(module)

    pages: list[Page] = []
    for path in sorted(pages_dir.glob("*.md")):
        meta, body = frontmatter.parse(path.read_text(encoding="utf-8"))
        slug = _slug_from_filename(path)
        url = "index.html" if slug == "index" else f"{slug}.html"
        pages.append(
            Page(
                kind="page",
                slug=slug,
                title=str(meta.get("title") or slug),
                summary=str(meta.get("summary") or ""),
                body=body,
                source=path,
                url=url,
                order=int(meta.get("order") or 999),
                meta=meta,
            )
        )
    pages.sort(key=lambda p: (p.order, p.slug))

    return Site(config=config, modules=modules, pages=pages, root=root)
