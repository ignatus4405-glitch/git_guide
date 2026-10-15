---
title: "Разбор: как собирается этот курс"
summary: "Практикум на исходниках курса: workflow проверки, тестов, сборки, проверки ссылок и публикации на GitHub Pages — с разбором каждой строки."
order: 3
updated: 2026-10-15
tags: [actions, ci, разбор, практика]
goals:
  - Прочитать и объяснить workflow проверки, тестов и сборки этого репозитория
  - Понять, как сборка передаётся в job публикации и как включается Pages
  - Уметь адаптировать этот пайплайн под свой проект
---

## Что мы разбираем

Курс, который вы читаете, живёт в этом же репозитории и собирается своими же workflows.
Ниже — структура пайплайнов; файлы лежат в `.github/workflows/`, их можно читать параллельно
с уроком.

```text title="Пайплайны репозитория"
ci.yml            push/PR:  validate → test → build (+ проверка ссылок, артефакт site-<sha>)
pages.yml         main:     build → deploy на GitHub Pages (job deploy только если Pages включён)
docs-sync.yml     main:     пересборка и коммит обновлённых docs/STATE.md и docs/MANIFEST.json
healthcheck.yml   пн 06:00: контрольная сборка; при падении создаёт issue
```

## ci.yml: три независимых проверки

```yaml title=".github/workflows/ci.yml (сокращённо)"
name: CI
on:
  push:
    branches: ["**"]
  pull_request:
  workflow_dispatch:
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true      # новые push отменяют устаревшие прогоны — экономим минуты

permissions:
  contents: read                # токену больше прав не нужно

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with: {python-version: "3.12"}
      - run: python3 tools/validate.py --strict
  test:
    runs-on: ubuntu-latest
    steps: [ checkout, setup-python, python3 tools/test_build.py ]
  build:
    needs: [validate, test]
    runs-on: ubuntu-latest
    steps:
      - checkout, setup-python
      - run: python3 build.py
      - run: python3 tools/validate.py --site site    # проверка всех внутренних ссылок
      - uses: actions/upload-artifact@v7
        with: {name: site-${{ github.sha }}, path: site/}
```

На что обратить внимание:

- **`concurrency`** отменяет устаревшие прогоны: пуши в одну ветку не тратят минуты впустую.
- **`--strict` в validate** превращает предупреждения о контенте в ошибку CI. Так качество поддерживается автоматически.
- **`build` зависит от `validate` и `test`**: сборка не запустится, если контент или код сломаны.
- **Артефакт с именем `site-<sha>`** можно скачать из интерфейса: удобно смотреть сборку из PR.
- **`permissions: contents: read`** — минимум прав, потому что для проверок больше не нужно.

## pages.yml: публикация сайта

```yaml title=".github/workflows/pages.yml (сокращённо)"
on:
  push: {branches: [main]}
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/configure-pages@v6
      - run: python3 build.py
      - uses: actions/upload-pages-artifact@v5
        with: {path: site}
  deploy:
    needs: build
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    permissions: {pages: write, id-token: write}
    runs-on: ubuntu-latest
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
```

Тонкости, которые видно только на практике:

- **`environment: github-pages`** связывает job с окружением Pages: там видно URL публикации и историю деплоев.
- **Права `pages: write` и `id-token: write`** обязательны: без OIDC-токена деплой не пройдёт.
- **`upload-pages-artifact` принимает ровно один каталог** (у нас `site/`), при этом сам артефакт
  обязан лежать в корне сайта — вложенные структуры ломают публикацию.
- **Pages должен быть включён** в Settings → Pages (Source: GitHub Actions). Если он выключен,
  деплой упадёт — это нормальный сигнал, что осталось одно ручное действие.

::: tip Как включить Pages
Settings → Pages → Build and deployment → Source: **GitHub Actions**. После этого следующий
push в `main` (или ручной запуск workflow `pages`) опубликует сайт по адресу
`https://<user>.github.io/<repo>/`. Альтернатива — включить через API (нужны права admin):
`gh api -X POST repos/OWNER/REPO/pages -f build_type=workflow`.
:::

## docs-sync.yml: документация обновляется сама

Любой агент (или человек), который продолжит работу, должен видеть актуальную карту репозитория.
Поэтому на каждый push в `main` workflow пересобирает курс и коммитит изменившиеся
`docs/STATE.md` и `docs/MANIFEST.json`:

```yaml title="Автокоммит документации (фрагмент)"
permissions:
  contents: write
steps:
  - uses: actions/checkout@v7
    with: {fetch-depth: 0}          # история нужна, чтобы даты файлов были верными
  - run: python3 build.py
  - run: |
      if git diff --quiet -- docs/; then
        echo "Документация уже актуальна"
      else
        git config user.name  "github-actions[bot]"
        git config user.email "actions@github.com"
        git add docs/
        git commit -m "docs: автообновление карты репозитория [skip ci]"
        git push
      fi
```

Комментарий `[skip ci]` в сообщении коммита обязателен: без него авто-коммит запустит
следующий прогон, и получится бесконечная петля.

## healthcheck.yml: расписание как страховка

```yaml title="Еженедельная проверка"
on:
  schedule:
    - cron: "0 6 * * 1"
  workflow_dispatch:
jobs:
  build:
    steps: [ checkout, setup-python, python3 build.py, python3 tools/validate.py --site site ]
  report:
    needs: build
    if: failure()
    permissions: {issues: write}
    steps:
      - run: |
          gh issue create --title "Еженедельная проверка курса: сборка падает" \
            --body "Прогон: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
        env: {GH_TOKEN: "${{ secrets.GITHUB_TOKEN }}"}
```

Ошибки внешнего мира (обновления зависимостей, изменения в API, устаревшие ссылки) проявляются
не в момент коммита, а позже. Расписание ловит их само — и открывает задачу вместо того, чтобы
ждать, пока кто-то нажмёт «собрать».

## Как адаптировать под свой проект

1. Скопируйте `ci.yml` и замените команды на свои (`npm ci && npm test`, `go test ./...`, …).
2. Оставьте три job-а: `validate` (линтеры), `test` (тесты), `build` (сборка + артефакт).
3. Включите `concurrency` и `permissions` — они одинаковы для большинства проектов.
4. Если есть сайт или бинарник — добавьте `upload-artifact`, а для публикации — отдельный workflow с `environment`.
5. Обязательные проверки закрепите в защите ветки: имя job-а должно совпадать с `contexts`.

## Итоги

- Пайплайн курса — рабочий пример настоящего CI: проверки, сборка, артефакт, публикация.
- `concurrency` + `permissions` + `needs` дают экономию минут и предсказуемый порядок.
- Публикация на Pages — два job-а: сборка и деплой, с окружением `github-pages`.
- Документация обновляется авто-коммитом с `[skip ci]`, чтобы не вызывать петлю.
- Расписание ловит деградации, которые не связаны с вашими коммитами.

::: exercise Упражнение: свой мини-пайплайн
1. Создайте репозиторий с любым статическим проектом (HTML-страница, скрипт на Python).
2. Настройте три job-а: `lint` (`tools/validate.py --strict` для курса или свой линтер),
   `test` (ваши тесты) и `build` (сборка + `upload-artifact`).
3. Добавьте `concurrency` и `permissions: contents: read`.
4. Включите Pages (Settings → Pages → Source: GitHub Actions) и добавьте job деплоя с окружением.
5. Проверьте, что после слияния в `main` сайт обновился, а артефакт сборки доступен в прогоне.
:::

::: quiz Зачем в workflow авто-коммита документации указывать `[skip ci]`?
- ( ) Чтобы коммит не подписывался ключом
- (x) Чтобы авто-коммит не запускал новый прогон workflow и не создал бесконечную петлю
- ( ) Чтобы секреты не попали в лог

GitHub ищет эту строку в сообщении коммита и пропускает запуск workflow по push.
Без неё авто-коммит вызывает новый прогон, тот снова коммитит — и так бесконечно.
:::
