"""Генерация документации состояния для людей и агентов.

``build.py`` вызывает :func:`write` и обновляет два файла в каталоге ``docs/``:

* ``docs/STATE.md`` — человекочитаемая «карта репозитория»: что уже сделано,
  как собирать, какие у проекта инварианты, что делать следующему агенту;
* ``docs/MANIFEST.json`` — машинный инвентарь: модули, уроки, страницы, схемы,
  метрики и контрольные суммы-заглушки для сверки CI.

Оба файла перезаписываются целиком, поэтому их нельзя править вручную: правьте
контент (``content/``) или код сборки (``tools/``) и запустите ``python3 build.py``.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import gen_diagrams
from .content import Site

BANNER = "<!-- ФАЙЛ СГЕНЕРИРОВАН АВТОМАТИЧЕСКИ (tools/gen_state.py) — НЕ ПРАВИТЬ ВРУЧНУЮ -->"


def _git(*args: str, root: Path | None = None) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=False, timeout=20
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return ""


def manifest(site: Site, info: dict, root: Path) -> dict:
    return {
        "$schema": "docs/manifest.schema.json",
        "project": {
            "title": site.config["title"],
            "version": site.config["version"],
            "repo": site.config["repo"],
            "base_url": site.config["base_url"],
            "license": site.config.get("license", "MIT"),
            "lang": site.config.get("lang", "ru"),
        },
        "build": {
            "command": "python3 build.py",
            "output": "site/",
            "built_at": info.get("built_at"),
            "revision": info.get("revision"),
            "branch": info.get("branch"),
            "files_written": len(info.get("files", [])),
            "warnings": info.get("warnings", []),
        },
        "stats": info.get("stats", {}),
        "modules": [
            {
                "id": module.id,
                "dir": f"content/{module.dir}",
                "title": module.title,
                "icon": module.icon,
                "level": module.level,
                "lessons": len(module.lessons),
                "minutes": module.minutes,
                "words": module.words,
                "quizzes": module.quizzes,
                "url": module.url,
            }
            for module in site.modules
        ],
        "lessons": [
            {
                "slug": lesson.slug,
                "module": lesson.module_id,
                "order": lesson.order,
                "title": lesson.title,
                "summary": lesson.summary,
                "url": lesson.url,
                "source": lesson.source.relative_to(root).as_posix(),
                "words": lesson.word_count,
                "minutes": lesson.reading_time,
                "code_blocks": lesson.code_blocks,
                "quizzes": lesson.quiz_count,
                "goals": lesson.goals,
                "tags": lesson.tags,
                "updated": lesson.meta.get("updated", ""),
            }
            for module in site.modules
            for lesson in module.lessons
        ],
        "pages": [
            {
                "slug": page.slug,
                "title": page.title,
                "url": page.url,
                "source": page.source.relative_to(root).as_posix(),
                "nav": str(page.meta.get("nav", "true")).lower() != "false",
                "order": page.order,
            }
            for page in site.pages
        ],
        "diagrams": [
            {
                "file": f"assets/img/diagrams/{name}",
                "generator": "tools/gen_diagrams.py",
                "function": gen_diagrams.DIAGRAMS[name].__name__,
            }
            for name in gen_diagrams.DIAGRAMS
        ],
        "infrastructure": {
            "site.yml": "метаданные сайта: заголовок, версия, базовый URL, цвета",
            "build.py": "точка входа сборки",
            "tools/": "модули сборки: markdown, подсветка, шаблоны, схемы, проверки",
            "assets/": "статические файлы: css, js, favicon (копируются в site/assets)",
            "content/": "учебный контент: modules.yml, модули с уроками, отдельные страницы",
            ".github/workflows/ci.yml": "проверка, самотесты и сборка на каждый push/PR",
            ".github/workflows/pages.yml": "публикация собранного сайта на GitHub Pages",
            ".github/workflows/docs-sync.yml": "автообновление docs/STATE.md и MANIFEST.json",
            ".github/workflows/healthcheck.yml": "еженедельная проверка сборки с созданием issue",
            "AGENTS.md": "правила работы для человека и агента: что делать после правок",
            "docs/CONTENT_GUIDE.md": "формат контента: front matter, врезки, схемы, квизы",
            "docs/ARCHITECTURE.md": "устройство генератора и как расширять",
            "docs/CHANGELOG.md": "журнал изменений курса",
        },
    }


def state_markdown(site: Site, info: dict, root: Path) -> str:
    stats = info.get("stats", {})
    cfg = site.config
    log = _git("log", "--pretty=format:%h · %cs · %s", "-n", "15", root=root) or "· история недоступна"
    files = _git("ls-files", root=root)
    tracked = len(files.splitlines()) if files else 0

    module_rows = "\n".join(
        f"| {idx} | {module.icon} `{module.id}` | {module.title} | {len(module.lessons)} | "
        f"{module.words} | ≈{module.minutes} мин | {module.quizzes} | `content/{module.dir}/` |"
        for idx, module in enumerate(site.modules, start=1)
    )
    lesson_rows = "\n".join(
        f"| `{lesson.slug}` | {lesson.module_id} | {lesson.order} | {lesson.title} | "
        f"{lesson.word_count} | ≈{lesson.reading_time} мин | {lesson.quiz_count} | "
        f"`{lesson.source.relative_to(root).as_posix()}` |"
        for module in site.modules
        for lesson in module.lessons
    )
    page_rows = "\n".join(
        f"| `{page.slug}` | {page.title} | `{page.url}` | {page.word_count} | "
        f"`{page.source.relative_to(root).as_posix()}` |"
        for page in site.pages
    )
    diagram_rows = "\n".join(
        f"| `{name}` | `{gen_diagrams.DIAGRAMS[name].__name__}()` |" for name in gen_diagrams.DIAGRAMS
    )
    warnings = info.get("warnings") or []
    warnings_block = (
        "\n".join(f"- ⚠️ {w}" for w in warnings) if warnings else "Предупреждений сборки нет. ✔"
    )

    return f"""{BANNER}

# Состояние репозитория: {cfg['title']}

> Этот файл — точка входа для любого, кто продолжает работу: человека или агента.
> Он генерируется командой `python3 build.py` (модуль `tools/gen_state.py`)
> и обновляется автоматически в GitHub Actions (workflow `docs-sync`).

## 1. Что это за проект

Учебный курс по Git и GitHub: {stats.get('lessons', 0)} уроков в {stats.get('modules', 0)} модулях,
≈{stats.get('minutes', 0)} минут чтения, {stats.get('quizzes', 0)} вопросов самопроверки,
{len(gen_diagrams.DIAGRAMS)} SVG-схем. Курс хранится как markdown, собирается в статический
сайт самим репозиторием: зависимостей нет, нужен только Python 3.10+.

* Версия: `{cfg['version']}` · лицензия: `{cfg.get('license', 'MIT')}`
* Репозиторий: {cfg['repo']}
* Сайт (после включения Pages): {cfg['base_url']}
* Последняя сборка: {info.get('built_at')} · ревизия `{info.get('revision')}` · ветка `{info.get('branch')}`
* Отслеживаемых git-файлов: {tracked} · записано при сборке: {len(info.get('files', []))}

## 2. Как собрать, проверить, посмотреть локально

```bash
python3 build.py                      # собрать сайт в ./site
python3 tools/validate.py             # проверки контента (CI: job validate)
python3 tools/validate.py --site site # проверки ссылок в собранном сайте
python3 tools/test_build.py           # самотесты сборки (CI: job test)
python3 tools/serve.py --port 8000    # предпросмотр: http://localhost:8000
python3 tools/new_lesson.py --help    # каркас нового урока
```

## 3. Как публикуется сайт

| Workflow | Когда запускается | Что делает |
| --- | --- | --- |
| `.github/workflows/ci.yml` | push в любую ветку, PR, вручную | `validate` → `test` → `build` (+ проверка ссылок, артефакт `site-<sha>`) |
| `.github/workflows/pages.yml` | push в `main`, вручную | сборка и публикация на GitHub Pages (если Pages включён) |
| `.github/workflows/docs-sync.yml` | push в `main`, вручную | пересобирает и коммитит обновлённые `docs/STATE.md`, `docs/MANIFEST.json` |
| `.github/workflows/healthcheck.yml` | по расписанию (пн 06:00 UTC) | контрольная сборка; при падении создаёт issue |

## 4. Состав курса

| № | Модуль | Название | Уроков | Слов | Чтение | Вопросов | Каталог |
| --- | --- | --- | --- | --- | --- | --- | --- |
{module_rows}

### Уроки

| slug | Модуль | № | Название | Слов | Время | 🧩 | Источник |
| --- | --- | --- | --- | --- | --- | --- | --- |
{lesson_rows}

### Отдельные страницы

| slug | Название | URL | Слов | Источник |
| --- | --- | --- | --- | --- |
{page_rows}

### Схемы (генерируются кодом)

| Файл | Функция |
| --- | --- |
{diagram_rows}

## 5. Карта кода и документации

| Путь | Назначение |
| --- | --- |
| `site.yml` | метаданные сайта и версия курса |
| `build.py` | сборка: контент → HTML, поиск, sitemap, feed, build-info |
| `tools/md.py` | Markdown → HTML: врезки, квизы, таблицы, код с подписями |
| `tools/highlight.py` | подсветка синтаксиса без зависимостей |
| `tools/templates.py` | HTML-каркас страницы, сайдбар, шапка, поиск |
| `tools/content.py` | модель контента: модули, уроки, страницы, ссылки |
| `tools/gen_diagrams.py` | SVG-схемы как код |
| `tools/validate.py` | проверки контента и ссылок (CI) |
| `tools/test_build.py` | самотесты сборки (CI) |
| `tools/gen_state.py` | этот файл и `docs/MANIFEST.json` |
| `content/modules.yml` | порядок и метаданные модулей |
| `content/<модуль>/*.md` | уроки: front matter + markdown |
| `AGENTS.md` | обязательный протокол работы для агентов |
| `docs/CONTENT_GUIDE.md` | синтаксис контента |
| `docs/ARCHITECTURE.md` | внутреннее устройство генератора |
| `docs/CHANGELOG.md` | журнал изменений |

## 6. Правила продолжения работы (обязательно)

1. **Соберите после каждой правки:** `python3 build.py`.
2. **Проверьте:** `python3 tools/validate.py --site site` и `python3 tools/test_build.py` — оба должны быть зелёными.
3. **Обновите журнал:** короткая запись в `docs/CHANGELOG.md` (дата, что изменено, зачем).
4. **Проверка:** в CI прогоняются те же команды; PR не должен ломать job `validate`, `test`, `build`.
5. **Не править вручную:** `site/`, `docs/STATE.md`, `docs/MANIFEST.json` — они генерируются.
6. **Ссылки внутри контента:** только через схемы `lesson:`, `page:`, `module:` — валидатор ловит битые.
7. **Схемы:** новые диаграммы добавляются функцией в `tools/gen_diagrams.py` и регистрируются в `DIAGRAMS`.

## 7. Что можно улучшить дальше (кандидаты в задачи)

- [ ] Добавить интерактивный тренажёр команд (`tools/simulator.py`: учебные сценарии git в браузере).
- [ ] Добавить английскую версию: `content-en/` + переключатель языка в шапке.
- [ ] Прогонять примеры из уроков в песочнице и сверять вывод (`tools/verify_snippets.py`).
- [ ] Добавить страницу «Экзамен» с проверкой ответов и сохранением результата.
- [ ] Собирать PDF-версию курса (`--pdf`) через печать браузера.

## 8. Текущее состояние сборки

* Записано файлов: {len(info.get('files', []))}
* Предупреждений: {len(warnings)}

{warnings_block}

## 9. Последние изменения репозитория

```
{log}
```

_Обновлено: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_
"""


def write(site: Site, info: dict, root: Path) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    docs.joinpath("STATE.md").write_text(state_markdown(site, info, root), encoding="utf-8")
    docs.joinpath("MANIFEST.json").write_text(
        json.dumps(manifest(site, info, root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
