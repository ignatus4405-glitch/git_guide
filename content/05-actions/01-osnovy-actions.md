---
title: "GitHub Actions: workflow, jobs, steps"
summary: "Анатомия workflow: события, задания, шаги, runner-ы, контексты и выражения. Первый рабочий пайплайн и разбор типичных ошибок."
order: 1
updated: 2026-10-15
tags: [actions, ci, yaml, workflow]
goals:
  - Объяснить структуру workflow: on, jobs, steps, runs-on
  - Настроить запуск по push, pull_request, расписанию и вручную
  - Использовать контексты github.*, secrets.* и условные выражения if
---

## Из чего состоит Actions

![Схема: пайплайн GitHub Actions](assets/img/diagrams/actions-pipeline.svg "Событие → задания → шаги → артефакт → публикация")

| Понятие | Что это |
| --- | --- |
| Workflow | файл в `.github/workflows/*.yml`, описывающий автоматизацию |
| Event (`on`) | что запускает workflow: push, PR, schedule, workflow_dispatch, release… |
| Job | набор шагов, выполняющихся на одном runner-е; по умолчанию jobs идут параллельно |
| Step | один шаг: либо `uses:` (готовое действие), либо `run:` (команда) |
| Runner | машина (`ubuntu-latest`, `windows-latest`, `macos-latest` или self-hosted) |
| Action | переиспользуемый блок из Marketplace или из вашего репозитория |
| Artifact | файл, сохранённый из прогона (логи, сборка, отчёты) |

## Первый workflow

```yaml title=".github/workflows/hello.yml"
name: Проверка приветствия

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:            # запуск вручную из интерфейса

permissions:
  contents: read                # минимальные права токена — принцип наименьших привилегий

jobs:
  hello:
    name: Поздороваться
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5        # копирует репозиторий на runner
      - name: Показать файлы
        run: ls -la
      - name: Проверить, что README не пустой
        run: test -s README.md
```

Ключевые детали:

- **`actions/checkout` обязателен**, иначе рабочая копия пустая: runner стартует «чистым».
- **Триггеры фильтруются**: `branches`, `paths`, `types`. Например, `paths: ['content/**']`
  запустит сборку только при изменении контента.
- **`workflow_dispatch`** даёт кнопку «Run workflow» и позволяет принимать входные параметры.
- **`permissions`** ограничивает `GITHUB_TOKEN`; без надобности не давайте `write-all`.

## Расписание и ручной запуск с параметрами

```yaml title="Триггеры"
on:
  schedule:
    - cron: "0 6 * * 1"          # каждый понедельник в 06:00 UTC
  workflow_dispatch:
    inputs:
      environment:
        description: "Куда публиковать"
        type: choice
        options: [staging, production]
        default: staging
```

Внутри шагов значения доступны через контексты:

```yaml title="Контексты и выражения"
- run: echo "Событие: ${{ github.event_name }}, ветка: ${{ github.ref_name }}, ревизия: ${{ github.sha }}"
- run: echo "Публикуем в ${{ github.event.inputs.environment }}"
  if: github.event_name == 'workflow_dispatch'
```

::: tip Отладка workflow
- `gh run list`, `gh run view --log-failed` — логи упавшего шага.
- `ACTIONS_STEP_DEBUG=true` (секрет в репозитории) включает подробные логи.
- Локально многие workflow воспроизводит `act` (`brew install act`) — но не всё, особенно Pages.
:::

## Порядок и зависимости

По умолчанию все jobs идут параллельно. Порядок задаётся через `needs`:

```yaml title="Цепочка задач"
jobs:
  validate:
    runs-on: ubuntu-latest
    steps: [ ... ]
  build:
    needs: validate          # начнётся только после успеха validate
    runs-on: ubuntu-latest
    steps: [ ... ]
  notify:
    needs: [validate, build]
    if: failure()            # выполнится только при падении предыдущих
    runs-on: ubuntu-latest
    steps:
      - run: echo "Что-то упало — проверьте логи"
```

Полезные функции условий: `success()`, `failure()`, `cancelled()`, `always()`.
`if: always()` нужен, например, чтобы загрузить артефакт даже после падения тестов.

## Типичные ошибки новичка

| Симптом | Причина | Решение |
| --- | --- | --- |
| `sh: 1: python: not found` | не установлен нужный рантайм | `actions/setup-python@v6` / `setup-node@v4` |
| Файлы не найдены | забыли `actions/checkout` или указан не тот каталог | добавить checkout, проверить `defaults.run.working-directory` |
| Workflow не запускается | неверный путь файла или отступ в YAML | файл строго в `.github/workflows/`, проверить YAML-линтером |
| `Permission denied` при push | у токена `contents: read` по умолчанию | явно указать `permissions: contents: write` (осторожно) |
| Долгая установка зависимостей | нет кэша | `actions/cache` или встроенный кэш `setup-*` |
| Секрет пустой | секрет не добавлен или используется в `if` без `env` | добавить в Settings → Secrets, передавать через `env` |

## Итоги

- Workflow = события + jobs + steps; jobs идут параллельно, `needs` задаёт порядок.
- `actions/checkout` нужен почти всегда; рантайм ставится через `setup-*`.
- Триггеры фильтруются по ветвям, путям и типам событий; ручной запуск — `workflow_dispatch`.
- Права токена ограничиваются блоком `permissions`.
- Отлаживайте через логи (`gh run view --log-failed`) и условные шаги `if: failure()`.

::: exercise Упражнение: свой первый workflow
1. Создайте `.github/workflows/hello.yml` с триггерами `push` и `workflow_dispatch`.
2. Добавьте шаг checkout и шаг, который печатает `github.ref_name`, `github.sha` и список файлов.
3. Добавьте второй job, зависящий от первого через `needs`, который проверяет, что README не пустой.
4. Запушьте ветку и посмотрите прогон через `gh run list` и `gh run watch`.
5. Запустите workflow вручную: `gh workflow run hello.yml` и убедитесь, что он появился в списке прогонов.
:::

::: quiz Зачем указывать `actions/checkout` в начале job?
- ( ) Чтобы установить зависимости проекта
- (x) Чтобы скопировать содержимое репозитория в рабочую директорию runner-а
- ( ) Чтобы включить кэширование между прогонами

Runner начинает работу с пустой машины: без `checkout` в рабочей директории нет файлов репозитория,
и команды сборки/тестов работать не будут.
:::
