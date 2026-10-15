"""HTML-шаблоны сайта курса.

Структура страницы::

    <body>
      <a class="skip">к содержимому</a>
      <header class="topbar">  логотип · поиск · прогресс · тема · GitHub
      <div class="layout">
        <aside class="sidebar">  оглавление курса (все модули и уроки)
        <main class="content">   хлебные крошки · заголовок · markdown · nav prev/next
        <aside class="toc">      оглавление текущего урока (scrollspy)
      <footer>  собрано действий GitHub Actions · дата сборки · версия
      <div class="search-results">  оверлей поиска
    """

from __future__ import annotations

import html
from datetime import datetime, timezone

from .content import Module, Page, Site


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def plural(count: int, one: str, few: str, many: str) -> str:
    """Русская форма множественного числа: 1 модуль, 2 модуля, 5 модулей."""
    count = abs(int(count))
    if count % 10 == 1 and count % 100 != 11:
        return one
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return few
    return many


def head(site: Site, page: Page, *, title: str | None = None, description: str | None = None) -> str:
    cfg = site.config
    page_title = title or (page.title if page.url != "index.html" else "")
    full_title = f"{page_title} · {cfg['short_title']}" if page_title else f"{cfg['title']}"
    desc = description or page.summary or cfg["description"]
    canonical = f"{cfg['base_url'].rstrip('/')}/{page.url}"
    return f"""<!DOCTYPE html>
<html lang="{_e(cfg['lang'])}" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(full_title)}</title>
<meta name="description" content="{_e(desc)}">
<meta name="author" content="{_e(cfg['author'])}">
<meta name="theme-color" content="{_e(cfg['theme']['accent'])}">
<link rel="canonical" href="{_e(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{_e(full_title)}">
<meta property="og:description" content="{_e(desc)}">
<meta property="og:url" content="{_e(canonical)}">
<meta property="og:site_name" content="{_e(cfg['title'])}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="{_e(cfg['title'])}" href="{page.prefix}feed.xml">
<link rel="stylesheet" href="{page.prefix}assets/css/site.css">
<link rel="icon" href="{page.prefix}assets/img/favicon.svg" type="image/svg+xml">
<script>
  // Тема применяется до первой отрисовки, чтобы не мигало при загрузке.
  try {{
    const saved = localStorage.getItem('gg-theme');
    const theme = saved || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.dataset.theme = theme;
  }} catch (e) {{}}
</script>
</head>
<body data-page="{_e(page.slug)}" data-kind="{_e(page.kind)}">
<a class="skip-link" href="#main">Перейти к содержимому</a>
"""


def topbar(site: Site, page: Page) -> str:
    cfg = site.config
    return f"""
<header class="topbar">
  <button class="icon-btn sidebar-toggle" type="button" data-sidebar-toggle aria-label="Оглавление курса" aria-expanded="false">
    <span class="burger"></span>
  </button>
  <a class="brand" href="{page.prefix}index.html">
    <span class="brand__mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M23.1 11.6 12.4.9A2 2 0 0 0 11-.1H2.5A2.5 2.5 0 0 0 0 2.4V11c0 .6.2 1.1.7 1.5l10.7 10.7a1.5 1.5 0 0 0 2.2 0l9.5-9.5a1.5 1.5 0 0 0 0-2.1ZM6.2 7.8A1.9 1.9 0 1 1 8 5.9a1.9 1.9 0 0 1-1.9 1.9Z"/></svg>
    </span>
    <span class="brand__text">
      <strong>{_e(cfg['short_title'])}</strong>
      <small>курс · {_e(cfg['version'])}</small>
    </span>
  </a>

  <button class="search-open" type="button" data-search-open>
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M10 2a8 8 0 1 0 4.9 14.3l5 5 1.4-1.4-5-5A8 8 0 0 0 10 2Zm0 2a6 6 0 1 1 0 12 6 6 0 0 1 0-12Z"/></svg>
    <span>Поиск по курсу</span>
    <kbd>/</kbd>
  </button>

  <div class="topbar__actions">
    <div class="progress" data-progress title="Прогресс по урокам сохраняется в этом браузере">
      <div class="progress__bar"><span data-progress-fill style="width:0%"></span></div>
      <span class="progress__text" data-progress-text>0%</span>
    </div>
    <button class="icon-btn" type="button" data-theme-toggle aria-label="Переключить тему">
      <span class="theme-sun" aria-hidden="true">☀</span><span class="theme-moon" aria-hidden="true">☾</span>
    </button>
    <a class="icon-btn" href="{_e(cfg['repo'])}" target="_blank" rel="noopener" aria-label="Репозиторий курса на GitHub" title="Репозиторий курса">
      <svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M8 0C3.6 0 0 3.6 0 8c0 3.5 2.3 6.5 5.5 7.6.4.1.5-.2.5-.4v-1.4c-2.2.5-2.7-1-2.7-1-.4-1-.9-1.2-.9-1.2-.7-.5.1-.5.1-.5.8.1 1.2.8 1.2.8.7 1.2 1.9.9 2.4.7.1-.5.3-.9.5-1.1-1.8-.2-3.6-.9-3.6-4 0-.9.3-1.6.8-2.2-.1-.2-.4-1 .1-2.1 0 0 .7-.2 2.2.8a7.6 7.6 0 0 1 4 0c1.5-1 2.2-.8 2.2-.8.4 1.1.2 1.9.1 2.1.5.6.8 1.3.8 2.2 0 3.1-1.9 3.8-3.6 4 .3.3.6.8.6 1.6v2.4c0 .2.1.5.5.4A8 8 0 0 0 16 8c0-4.4-3.6-8-8-8Z"/></svg>
    </a>
  </div>
</header>
"""


def sidebar(site: Site, page: Page) -> str:
    parts: list[str] = ['<nav class="sidebar" data-sidebar aria-label="Навигация по курсу">']
    parts.append('<div class="sidebar__inner">')
    parts.append('<p class="sidebar__label">Модули курса</p>')
    parts.append("<ol class=\"modules\">")
    for module in site.modules:
        active = " is-active" if page.module_id == module.id else ""
        parts.append(f'<li class="module{active}">')
        parts.append(
            f'<a class="module__link" href="{page.prefix}{module.url}">'
            f'<span class="module__icon" aria-hidden="true">{_e(module.icon)}</span>'
            f'<span class="module__title">{_e(module.title)}</span></a>'
        )
        parts.append('<ol class="lessons">')
        for lesson in module.lessons:
            cls = "lesson"
            if lesson.slug == page.slug:
                cls += " is-current"
            if lesson.quiz_count:
                cls += " has-quiz"
            parts.append(
                f'<li class="{cls}">'
                f'<label class="lesson__check" title="Отметить урок пройденным">'
                f'<input type="checkbox" data-lesson-check="{_e(lesson.slug)}"></label>'
                f'<a class="lesson__link" href="{page.prefix}{lesson.url}">'
                f'<span class="lesson__num">{lesson.order if lesson.order < 999 else "·"}</span>'
                f'<span class="lesson__title">{_e(lesson.title)}</span></a></li>'
            )
        parts.append("</ol></li>")
    parts.append("</ol>")
    parts.append('<p class="sidebar__label">Материалы</p><ul class="pages">')
    for item in site.pages:
        if str(item.meta.get("nav", "true")).lower() == "false":
            continue
        cls = " is-current" if item.slug == page.slug else ""
        label = item.meta.get("nav_title") or item.title
        parts.append(
            f'<li class="page{cls}"><a href="{page.prefix}{item.url}">'
            f'<span aria-hidden="true">{_e(item.meta.get("icon", "•"))}</span> {_e(label)}</a></li>'
        )
    parts.append(
        f'<li class="page"><a href="{_e(site.config["repo"])}" target="_blank" rel="noopener">'
        f'<span aria-hidden="true">🐙</span> Исходники курса</a></li>'
    )
    parts.append("</ul>")
    parts.append(
        '<p class="sidebar__hint">Курс собирается автоматически: каждый push '
        "запускает проверки и публикацию (GitHub Actions).</p>"
    )
    parts.append("</div></nav>")
    return "\n".join(parts)


def breadcrumbs(site: Site, page: Page) -> str:
    if page.url == "index.html":
        return ""
    parts = [f'<a href="{page.prefix}index.html">Курс</a>']
    if page.module_id:
        module = site.module_by_id(page.module_id)
        if module:
            parts.append(f'<a href="{page.prefix}{module.url}">{_e(module.title)}</a>')
    parts.append(f'<span aria-current="page">{_e(page.title)}</span>')
    return '<nav class="crumbs" aria-label="Хлебные крошки">' + '<span class="sep">/</span>'.join(parts) + "</nav>"


def lesson_meta_bar(site: Site, page: Page) -> str:
    if page.kind != "lesson":
        return ""
    repo = site.config["repo"]
    branch = site.config.get("repo_branch", "main")
    src = f"{repo}/blob/{branch}/{page.source.relative_to(site.root).as_posix()}"
    badges = [
        f'<span class="meta__item" title="Время чтения">⏱ ~{page.reading_time} мин</span>',
        f'<span class="meta__item" title="Объём">📄 {page.word_count} слов</span>',
    ]
    if page.code_blocks:
        badges.append(f'<span class="meta__item" title="Блоков кода">⌨ {page.code_blocks}</span>')
    if page.quiz_count:
        badges.append(f'<span class="meta__item" title="Вопросов для самопроверки">🧩 {page.quiz_count}</span>')
    if page.updated:
        badges.append(f'<span class="meta__item" title="Дата последнего изменения">🗓 {_e(page.updated)}</span>')
    badges.append(
        f'<a class="meta__item meta__item--link" href="{_e(src)}" target="_blank" rel="noopener">✎ Исходник урока</a>'
    )
    complete = (
        f'<label class="meta__complete"><input type="checkbox" data-lesson-check="{_e(page.slug)}">'
        "Урок пройден</label>"
    )
    return f'<div class="lesson-meta">{"".join(badges)}{complete}</div>'


def goals(site: Site, page: Page) -> str:
    if not page.goals:
        return ""
    items = "".join(f"<li>{_e(g)}</li>" for g in page.goals)
    return f'<div class="goals"><p class="goals__head">🎯 Что вы будете уметь</p><ul>{items}</ul></div>'


def toc(entries: list[dict]) -> str:
    if not entries:
        return ""
    items = "".join(
        f'<li class="toc__lvl{e["level"]}"><a href="#{e["id"]}">{_e(e["text"])}</a></li>'
        for e in entries
    )
    return (
        '<aside class="toc" data-toc aria-label="Содержание страницы">'
        '<p class="toc__label">На этой странице</p>'
        f'<ul>{items}</ul>'
        '<p class="toc__top"><a href="#top">↑ Наверх</a></p></aside>'
    )


def lesson_nav(site: Site, page: Page) -> str:
    if page.kind != "lesson":
        return ""
    prev, nxt = site.neighbours(page)
    blocks = []
    if prev:
        blocks.append(
            f'<a class="pn pn--prev" href="{page.prefix}{prev.url}"><span>← Предыдущий</span>'
            f"<strong>{_e(prev.title)}</strong></a>"
        )
    else:
        blocks.append('<span class="pn pn--empty"></span>')
    if nxt:
        blocks.append(
            f'<a class="pn pn--next" href="{page.prefix}{nxt.url}"><span>Следующий →</span>'
            f"<strong>{_e(nxt.title)}</strong></a>"
        )
    else:
        blocks.append(
            f'<a class="pn pn--next" href="{page.prefix}ekzamen.html"><span>Дальше →</span>'
            "<strong>Итоговый экзамен курса</strong></a>"
        )
    return f'<nav class="lesson-nav">{"".join(blocks)}</nav>'


def search_overlay(site: Site, page: Page) -> str:
    return f"""
<div class="search" data-search hidden>
  <div class="search__panel" role="dialog" aria-modal="true" aria-label="Поиск по курсу">
    <div class="search__field">
      <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M10 2a8 8 0 1 0 4.9 14.3l5 5 1.4-1.4-5-5A8 8 0 0 0 10 2Zm0 2a6 6 0 1 1 0 12 6 6 0 0 1 0-12Z"/></svg>
      <input type="search" data-search-input placeholder="Например: rebase, конфликт, Actions, PAT" autocomplete="off">
      <kbd>Esc</kbd>
    </div>
    <ul class="search__results" data-search-results></ul>
    <p class="search__hint">Ищите по всем урокам курса. ↑ ↓ — выбор, Enter — открыть.</p>
  </div>
</div>
"""


def footer(site: Site, page: Page, *, build_time: str, revision: str) -> str:
    cfg = site.config
    stats = site.stats()
    return f"""
<footer class="footer">
  <div class="footer__grid">
    <div>
      <p class="footer__title">{_e(cfg['title'])}</p>
      <p class="footer__text">
        {stats['modules']} {plural(stats['modules'], 'модуль', 'модуля', 'модулей')} ·
        {stats['lessons']} {plural(stats['lessons'], 'урок', 'урока', 'уроков')} ·
        {stats['quizzes']} {plural(stats['quizzes'], 'вопрос', 'вопроса', 'вопросов')} самопроверки ·
        ≈{stats['minutes']} {plural(stats['minutes'], 'минута', 'минуты', 'минут')} чтения
      </p>
    </div>
    <div>
      <p class="footer__title">Сборка</p>
      <p class="footer__text">
        GitHub Actions · {_e(build_time)} · версия {_e(cfg['version'])} ·
        <a href="{_e(cfg['repo'])}/commits/{_e(cfg.get('repo_branch', 'main'))}">история курса</a>
      </p>
    </div>
    <div>
      <p class="footer__title">Материалы</p>
      <p class="footer__text">
        <a href="{page.prefix}shpargalka.html">Шпаргалка</a> ·
        <a href="{page.prefix}slovar.html">Словарь</a> ·
        <a href="{page.prefix}oshibki.html">Ошибки</a> ·
        <a href="{page.prefix}karta-kursa.html">Карта курса</a>
      </p>
    </div>
  </div>
  <p class="footer__note">
    Текст курса — markdown в каталоге <code>content/</code>, схемы — код в
    <code>tools/gen_diagrams.py</code>, сборка — <code>python3 build.py</code>.
    Лицензия: {_e(cfg.get('license', 'MIT'))}. Сборка {_e(revision)}.
  </p>
</footer>
<script src="{page.prefix}assets/js/app.js" defer></script>
"""


def page_shell(
    site: Site,
    page: Page,
    *,
    body_html: str,
    toc_entries: list[dict],
    build_time: str,
    revision: str,
    title: str | None = None,
    description: str | None = None,
    extra_top: str = "",
) -> str:
    return (
        head(site, page, title=title, description=description)
        + topbar(site, page)
        + '<div class="layout">'
        + sidebar(site, page)
        + '<div class="layout__underlay" data-sidebar-underlay hidden></div>'
        + f'<main class="content" id="main"><a id="top"></a>{extra_top}'
        + breadcrumbs(site, page)
        + f"<article class=\"prose\">{body_html}</article>"
        + lesson_nav(site, page)
        + "</main>"
        + toc(toc_entries)
        + "</div>"
        + search_overlay(site, page)
        + footer(site, page, build_time=build_time, revision=revision)
        + "</body></html>\n"
    )


def module_overview_html(site: Site, module: Module, page: Page) -> str:
    """Автоматическая страница модуля, если в content/<модуль>/ нет index.md."""
    items = []
    for lesson in module.lessons:
        items.append(
            f'<li class="card-list__item">'
            f'<a href="{page.prefix}{lesson.url}">'
            f'<span class="card-list__num">{lesson.order if lesson.order < 999 else "·"}</span>'
            f'<span><strong>{_e(lesson.title)}</strong>'
            f'<small>{_e(lesson.summary)}</small>'
            f'<span class="tagline">~{lesson.reading_time} мин'
            + (f" · 🧩 {lesson.quiz_count}" if lesson.quiz_count else "")
            + "</span></span></a></li>"
        )
    return (
        f'<h1>{_e(module.title)}</h1>'
        f'<p class="lead">{_e(module.description)}</p>'
        f'<ul class="card-list">{"".join(items)}</ul>'
    )


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
