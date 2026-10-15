<!-- ФАЙЛ СГЕНЕРИРОВАН АВТОМАТИЧЕСКИ (tools/gen_state.py) — НЕ ПРАВИТЬ ВРУЧНУЮ -->

# Состояние репозитория: Git и GitHub: полный курс

> Этот файл — точка входа для любого, кто продолжает работу: человека или агента.
> Он генерируется командой `python3 build.py` (модуль `tools/gen_state.py`)
> и обновляется автоматически в GitHub Actions (workflow `docs-sync`).

## 1. Что это за проект

Учебный курс по Git и GitHub: 24 урока
в 8 модулях,
≈99 минут чтения,
24 вопроса самопроверки,
13 SVG-схем. Курс хранится как markdown, собирается в статический
сайт самим репозиторием: зависимостей нет, нужен только Python 3.10+.

* Версия: `1.0.0` · лицензия: `MIT`
* Репозиторий: https://github.com/ignatus4405-glitch/git_guide
* Сайт (после включения Pages): https://ignatus4405-glitch.github.io/git_guide
* Последняя сборка: 2026-10-15 20:57 UTC · ревизия `e517b7f` · ветка `arena/0008ff39-git-guide`
* Отслеживаемых git-файлов: 81 · записано при сборке: 44

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
| 1 | 🌱 `git-osnovy` | Основы Git | 3 | 1622 | ≈10 мин | 3 | `content/01-osnovy/` |
| 2 | 🌿 `istoriya` | История, ветки, отмена | 4 | 1772 | ≈11 мин | 4 | `content/02-istoriya/` |
| 3 | 🐙 `github` | GitHub: репозитории и Pull Request | 3 | 1503 | ≈9 мин | 3 | `content/03-github/` |
| 4 | 🤝 `komanda` | Командная работа | 2 | 1090 | ≈7 мин | 2 | `content/04-komanda/` |
| 5 | ⚙️ `actions` | GitHub Actions: CI/CD | 3 | 1546 | ≈10 мин | 3 | `content/05-actions/` |
| 6 | 🚀 `pages` | Публикация на GitHub Pages | 2 | 926 | ≈6 мин | 2 | `content/06-pages/` |
| 7 | 🛡️ `bezopasnost` | Безопасность и секреты | 3 | 1643 | ≈10 мин | 3 | `content/07-bezopasnost/` |
| 8 | 🧙 `prodvinutye` | Продвинутые приёмы | 4 | 2036 | ≈13 мин | 4 | `content/08-prodvinutye/` |

### Уроки

| slug | Модуль | № | Название | Слов | Время | 🧩 | Источник |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `chto-takoe-git` | git-osnovy | 1 | Что такое Git и зачем нужен GitHub | 561 | ≈4 мин | 1 | `content/01-osnovy/01-chto-takoe-git.md` |
| `ustanovka-i-nastroyka` | git-osnovy | 2 | Установка и настройка Git | 505 | ≈3 мин | 1 | `content/01-osnovy/02-ustanovka-i-nastroyka.md` |
| `pervyy-repozitoriy` | git-osnovy | 3 | Первый репозиторий и первый коммит | 556 | ≈3 мин | 1 | `content/01-osnovy/03-pervyy-repozitoriy.md` |
| `istoriya-i-log` | istoriya | 1 | История коммитов: как читать git log | 403 | ≈3 мин | 1 | `content/02-istoriya/01-istoriya-i-log.md` |
| `vetki-i-sliyaniya` | istoriya | 2 | Ветки и слияния | 470 | ≈3 мин | 1 | `content/02-istoriya/02-vetki-i-sliyaniya.md` |
| `konflikty` | istoriya | 3 | Конфликты слияния: разбор без паники | 499 | ≈3 мин | 1 | `content/02-istoriya/03-konflikty.md` |
| `otmena-i-rebase` | istoriya | 4 | rebase, отмена и спасение работы | 400 | ≈2 мин | 1 | `content/02-istoriya/04-otmena-i-rebase.md` |
| `remote-i-sinhronizatsiya` | github | 1 | Удалённые репозитории и синхронизация | 450 | ≈3 мин | 1 | `content/03-github/01-remote-i-sinhronizatsiya.md` |
| `pull-request` | github | 2 | Pull Request: полный цикл | 521 | ≈3 мин | 1 | `content/03-github/02-pull-request.md` |
| `gh-cli-i-flow` | github | 3 | GitHub Flow и gh CLI | 532 | ≈3 мин | 1 | `content/03-github/03-gh-cli-i-flow.md` |
| `code-review` | komanda | 1 | Code review: как проверять и как просить проверку | 581 | ≈4 мин | 1 | `content/04-komanda/01-code-review.md` |
| `issues-i-proekty` | komanda | 2 | Issues, Projects и шаблоны репозитория | 509 | ≈3 мин | 1 | `content/04-komanda/02-issues-i-proekty.md` |
| `osnovy-actions` | actions | 1 | GitHub Actions: workflow, jobs, steps | 476 | ≈3 мин | 1 | `content/05-actions/01-osnovy-actions.md` |
| `matrica-kesh-artefakty` | actions | 2 | Матрицы, кэш, артефакты и секреты | 492 | ≈3 мин | 1 | `content/05-actions/02-matrica-kesh-artefakty.md` |
| `ci-kursa` | actions | 3 | Разбор: как собирается этот курс | 578 | ≈4 мин | 1 | `content/05-actions/03-ci-kursa.md` |
| `pages-osnovy` | pages | 1 | GitHub Pages: что это и как включить | 419 | ≈3 мин | 1 | `content/06-pages/01-pages-osnovy.md` |
| `deploy-iz-actions` | pages | 2 | Публикация из GitHub Actions | 507 | ≈3 мин | 1 | `content/06-pages/02-deploy-iz-actions.md` |
| `autentifikatsiya` | bezopasnost | 1 | Аутентификация: ключи, токены, 2FA | 538 | ≈3 мин | 1 | `content/07-bezopasnost/01-autentifikatsiya.md` |
| `sekrety-i-peremennye` | bezopasnost | 2 | Секреты в Actions и защита от утечек | 529 | ≈3 мин | 1 | `content/07-bezopasnost/02-sekrety-i-peremennye.md` |
| `istorii-i-utechki` | bezopasnost | 3 | История репозитория и утечки | 576 | ≈4 мин | 1 | `content/07-bezopasnost/03-istorii-i-utechki.md` |
| `hooki-i-shablon` | prodvinutye | 1 | Хуки, шаблоны и .gitattributes | 438 | ≈3 мин | 1 | `content/08-prodvinutye/01-hooki-i-shablon.md` |
| `bolshie-fayly-i-podmoduli` | prodvinutye | 2 | Большие файлы, LFS, подмодули и частичные клоны | 517 | ≈3 мин | 1 | `content/08-prodvinutye/02-bolshie-fayly-i-podmoduli.md` |
| `tegi-relizy-semver` | prodvinutye | 3 | Теги, релизы и semver | 517 | ≈3 мин | 1 | `content/08-prodvinutye/03-tegi-relizy-semver.md` |
| `git-iznutri` | prodvinutye | 4 | Git изнутри: объекты, ссылки, упаковка | 564 | ≈4 мин | 1 | `content/08-prodvinutye/04-git-iznutri.md` |

### Отдельные страницы

| slug | Название | URL | Слов | Источник |
| --- | --- | --- | --- | --- |
| `karta-kursa` | Карта курса | `karta-kursa.html` | 211 | `content/pages/karta-kursa.md` |
| `shpargalka` | Шпаргалка по Git и GitHub | `shpargalka.html` | 156 | `content/pages/shpargalka.md` |
| `slovar` | Словарь терминов | `slovar.html` | 747 | `content/pages/slovar.md` |
| `oshibki` | 20 типичных ошибок и как их исправить | `oshibki.html` | 378 | `content/pages/oshibki.md` |
| `ekzamen` | Итоговый экзамен курса | `ekzamen.html` | 1616 | `content/pages/ekzamen.md` |
| `resursy` | Материалы и что дальше | `resursy.html` | 359 | `content/pages/resursy.md` |
| `index` | Курс «Git и GitHub» | `index.html` | 393 | `content/pages/index.md` |

### Схемы (генерируются кодом)

| Файл | Функция |
| --- | --- |
| `three-trees.svg` | `three_trees()` |
| `commit-internals.svg` | `commit_internals()` |
| `branches-merge.svg` | `branches_merge()` |
| `merge-vs-rebase.svg` | `merge_vs_rebase()` |
| `conflict-resolution.svg` | `conflict_resolution()` |
| `reset-vs-revert.svg` | `reset_vs_revert()` |
| `remote-and-pr.svg` | `remote_and_pr()` |
| `actions-pipeline.svg` | `actions_pipeline()` |
| `workflows-compare.svg` | `workflows_compare()` |
| `security-layers.svg` | `security_layers()` |
| `lesson-anatomy.svg` | `lesson_anatomy()` |
| `fork-sync.svg` | `fork_sync()` |
| `large-files.svg` | `submodule_or_lfs()` |

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

* Записано файлов: 44
* Предупреждений: 0

Предупреждений сборки нет. ✔

## 9. Последние изменения репозитория

```
e517b7f · 2026-10-15 · fix(build): воспроизводимая сборка квизов и корректная разметка иллюстраций
29f8651 · 2026-10-15 · fix(ci): исправить невалидный YAML в pages.yml и обновить версии действий
f2b86d4 · 2026-10-15 · docs: README, протокол работы для агентов и документация по проекту
c0ee928 · 2026-10-15 · ci(actions): CI, публикация на Pages, синхронизация документации, healthcheck
d797733 · 2026-10-15 · feat(content): курс из 8 модулей, 24 уроков и справочных страниц
abe3745 · 2026-10-15 · feat(build): генератор статического сайта курса без зависимостей
4465386 · 2026-10-15 · Initial commit
```

_Обновлено: 2026-10-15 20:57 UTC_
