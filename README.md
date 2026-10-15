# Git и GitHub: полный курс

[![CI](https://github.com/ignatus4405-glitch/git_guide/actions/workflows/ci.yml/badge.svg)](https://github.com/ignatus4405-glitch/git_guide/actions/workflows/ci.yml)
[![Публикация на GitHub Pages](https://github.com/ignatus4405-glitch/git_guide/actions/workflows/pages.yml/badge.svg)](https://github.com/ignatus4405-glitch/git_guide/actions/workflows/pages.yml)
[![Лицензия: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Учебный курс по Git и GitHub с диаграммами, разборами команд, упражнениями и проверками
понимания. Курс — настоящий инженерный проект: контент лежит в markdown, схемы генерируются
кодом, сайт собирается и проверяется автоматически в GitHub Actions.

* **24 урока в 8 модулях** — от первого коммита до CI/CD, Pages, безопасности и внутреннего
  устройства Git.
* **13 схем**, описанных кодом в `tools/gen_diagrams.py` (никаких бинарных картинок в истории).
* **Проверяемый контент**: валидатор ищет битые ссылки, короткие уроки, непарные блоки,
  квизы без верного ответа (105 проверок), а сборка запускает 35 самотестов.
* **Без зависимостей**: нужен только Python 3.10+ и стандартная библиотека.

## Быстрый старт

```bash
git clone https://github.com/ignatus4405-glitch/git_guide.git
cd git_guide

python3 build.py                     # собрать сайт в ./site
python3 tools/serve.py --port 8000   # открыть http://localhost:8000
python3 tools/validate.py --site site --strict   # проверки контента и ссылок
python3 tools/test_build.py          # самотесты генератора (35 тестов)
```

Полезные команды:

```bash
python3 tools/new_lesson.py --list                       # список модулей курса
python3 tools/new_lesson.py --module actions --title "…"  # каркас нового урока
python3 tools/gen_diagrams.py --out /tmp/svg             # только схемы
python3 build.py --out public --strict                   # сборка в другой каталог
```

## Структура репозитория

```text
content/                 учебный материал
  modules.yml            порядок и метаданные модулей
  01-osnovy/ … 08-prodvinutye/   уроки по модулям (markdown + front matter)
  pages/                 карта курса, шпаргалка, словарь, ошибки, экзамен, ресурсы
tools/                   генератор: markdown, подсветка, шаблоны, схемы, проверки, тесты
assets/                  статические файлы сайта: css, js, favicon
build.py                 точка входа сборки
site.yml                 метаданные сайта и версия курса
docs/                    документация: архитектура, формат контента, состояние репозитория
.github/workflows/       CI, публикация на Pages, синхронизация документации, healthcheck
AGENTS.md                протокол работы: что обновлять после каждого изменения
```

## Состав курса

| № | Модуль | О чём | Уроков |
| --- | --- | --- | --- |
| 1 | 🌱 Основы Git | зачем нужен контроль версий, настройка, первый коммит | 3 |
| 2 | 🌿 История, ветки, отмена | git log, ветки, конфликты, rebase, reflog | 4 |
| 3 | 🐙 GitHub: репозитории и PR | remote, синхронизация, Pull Request, gh CLI | 3 |
| 4 | 🤝 Командная работа | code review, Issues, Projects, шаблоны | 2 |
| 5 | ⚙️ GitHub Actions: CI/CD | workflow, матрицы, кэш, артефакты, секреты | 3 |
| 6 | 🚀 Публикация на Pages | источники публикации, deploy из Actions, домен | 2 |
| 7 | 🛡️ Безопасность и секреты | ключи и токены, secrets, чистка истории | 3 |
| 8 | 🧙 Продвинутые приёмы | хуки, LFS и подмодули, релизы, устройство Git | 4 |

Актуальный состав с метриками — в [`docs/STATE.md`](docs/STATE.md) (генерируется сборкой).

## Как работает CI/CD

| Workflow | Запуск | Что делает |
| --- | --- | --- |
| `.github/workflows/ci.yml` | push в любую ветку, PR, вручную | `validate` → `test` → `build` + проверка ссылок + артефакт `site-<sha>` |
| `.github/workflows/pages.yml` | push в `main`, вручную | собирает сайт и публикует на GitHub Pages |
| `.github/workflows/docs-sync.yml` | push в `main`, вручную | пересобирает и коммитит `docs/STATE.md`, `docs/MANIFEST.json` |
| `.github/workflows/healthcheck.yml` | по понедельникам, вручную | контрольная сборка; при сбое создаёт issue |

### Включение публикации (одно ручное действие)

**Settings → Pages → Build and deployment → Source: GitHub Actions.**
После этого push в `main` публикует курс по адресу
`https://ignatus4405-glitch.github.io/git_guide/`.
Пока Pages выключен, workflow `pages.yml` пропускает деплой и пишет подсказку в сводку прогона.

## Что делает сборка

```text
content/**.md ─┐
tools/gen_diagrams.py ─┤
assets/ ───────┴─► build.py ─► site/ (HTML, search-index.json, sitemap.xml, feed.xml, 404.html)
                              └─► docs/STATE.md, docs/MANIFEST.json
```

Рендер страниц поддерживает: блоки кода с подписью и подсветкой, врезки (`::: tip`),
интерактивные вопросы самопроверки (`::: quiz`), таблицы, схемы-картинки с подписями,
токены `[[STATS]]` / `[[MODULE_MAP]]`, поиск, оглавление и прогресс в браузере.

## Как продолжить работу

1. Прочитайте [`AGENTS.md`](AGENTS.md) — это обязательный протокол: инварианты, чек-лист, формат коммитов.
2. Посмотрите [`docs/STATE.md`](docs/STATE.md) — актуальный состав курса и список идей развития.
3. Формат контента описан в [`docs/CONTENT_GUIDE.md`](docs/CONTENT_GUIDE.md),
   устройство генератора — в [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
4. Историю изменений ведите в [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

## Лицензия

[MIT](LICENSE) — используйте материалы курса, генератор и схемы как угодно.
