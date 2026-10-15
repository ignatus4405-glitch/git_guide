---
title: "Публикация из GitHub Actions"
summary: "Полный workflow сборки и деплоя на Pages: шаги, права, окружение, артефакт, откат и диагностика проблем публикации."
order: 2
updated: 2026-10-15
tags: [pages, actions, deploy, ci]
goals:
  - Собрать workflow публикации на Pages с job-ами build и deploy
  - Объяснить, зачем нужны permissions pages: write и id-token: write
  - Диагностировать и откатывать неудачные публикации
---

## Полный рабочий workflow

```yaml title=".github/workflows/pages.yml"
name: Публикация сайта на GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read      # читаем код для сборки
  pages: write        # публикуем артефакт в Pages
  id-token: write     # OIDC-токен для деплоя

concurrency:
  group: pages
  cancel-in-progress: false   # публикации не отменяем: пусть завершатся по порядку

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Собрать сайт
        run: python3 build.py
      - name: Проверить ссылки в собранном сайте
        run: python3 tools/validate.py --site site
      - name: Конфигурация Pages
        uses: actions/configure-pages@v5
      - name: Загрузить артефакт
        uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    permissions:
      pages: write
      id-token: write
    steps:
      - name: Опубликовать
        id: deployment
        uses: actions/deploy-pages@v4
```

## Что здесь происходит по шагам

| Шаг | Смысл |
| --- | --- |
| `permissions` | без `pages: write` GitHub откажет в публикации, без `id-token: write` не выдаст OIDC-токен |
| `concurrency: pages` | гарантирует, что два деплоя не наложатся друг на друга |
| `build` | собирает статику; здесь же прогоняются проверки ссылок |
| `configure-pages` | считывает настройки Pages и отдаёт их в `steps.*.outputs` |
| `upload-pages-artifact` | упаковывает каталог сборки; важен именно **один** корневой каталог |
| `environment: github-pages` | связывает job с окружением, даёт URL и историю публикаций |
| `deploy-pages` | собственно публикация; возвращает `page_url` |

::: tip Как передать параметры Pages в сборку
`actions/configure-pages@v5` с `id: pages` даёт `steps.pages.outputs.base_path` — удобно,
если генератор умеет принимать базовый путь. Тогда сайт корректно работает из подкаталога.
:::

## Диагностика

```bash title="Что смотреть, если публикация упала"
gh run list --workflow=pages.yml --limit 5
gh run view <run-id> --log-failed
gh api repos/OWNER/REPO/pages --jq '{status, html_url, source}'      # состояние Pages
gh api repos/OWNER/REPO/pages/builds --jq '.[0] | {status, error: .error.message}'
```

| Симптом | Причина | Решение |
| --- | --- | --- |
| `Get Pages site failed` | Pages не включён | Settings → Pages → Source: GitHub Actions |
| `Not Found` в deploy | нет прав `pages: write` / `id-token: write` | добавить `permissions` |
| `Artifact path is not valid` | каталог сборки не существует | убедиться, что сборка запускалась до загрузки |
| Сайт пустой, но job зелёный | артефакт собран из вложенного каталога | путь должен быть корнем сайта |
| 404 на внутренних ссылках | абсолютные пути вместо относительных | использовать относительные |
| Домен сбрасывается | нет `CNAME` в сборке | добавлять `CNAME` при сборке |

## Откат и повторная публикация

```bash title="Вернуться к предыдущей версии"
git revert <sha>                # отменяем проблемный коммит
git push                        # workflow опубликует исправленную версию
gh run rerun <run-id> --failed  # или повторить только упавшие job-ы
gh workflow run pages.yml       # ручной запуск публикации без изменений в коде
```

Полезная привычка: **проверять итог в браузере**. Зелёный деплой не гарантирует, что сайт
правильно отображается: например, забытая картинка не ломает сборку, но видна посетителю.

::: warning Не публикуйте секреты вместе с сайтом
Всё, что попало в каталог сборки, доступно публично. Проверяйте, что в артефакт не попали
`.env`, ключи, внутренние отчёты и черновики. В этом курсе каталог `site/` генерируется целиком
из `content/` и `assets/` — лишнего там не появится по построению.
:::

## Кэш и оптимизация

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

Для сайтов, собираемых из markdown, время сборки обычно меньше минуты, и кэш не нужен.
Оптимизировать стоит другое: `paths`-фильтры, чтобы не пересобирать сайт при изменении
файлов, не влияющих на результат (например, только `docs/`). Но помните: экономия минут
не должна приводить к публикации устаревшего контента.

## Итоги

- Публикация на Pages — два job-а: сборка с артефактом и деплой с окружением `github-pages`.
- Нужны права `pages: write` и `id-token: write`; порядок обеспечивает `concurrency: pages`.
- Диагностика: `gh run view --log-failed` и `gh api .../pages/builds`.
- Откат — обычный `git revert` и повторный push; публикация идёт за коммитом.
- Проверяйте результат глазами: успешный деплой не означает корректный сайт.

::: exercise Упражнение: публикация своими руками
1. Добавьте в свой репозиторий `pages.yml` из урока и запушьте в `main`.
2. Если деплой упал из-за выключенного Pages — включите его и запустите workflow вручную
   (`gh workflow run pages.yml`).
3. Откройте ссылку из окружения и проверьте три страницы: главную, любую внутреннюю, 404.
4. Испортите намеренно одну ссылку в контенте, запушьте и убедитесь, что job проверки упал
   и публикация не состоялась. Исправьте и убедитесь, что всё снова зелёное.
5. Проверьте `gh api repos/OWNER/REPO/pages/builds --jq '.[0].status'` — там должна быть последняя публикация.
:::

::: quiz Зачем нужен `id-token: write` в workflow публикации?
- ( ) Чтобы подписывать коммиты
- (x) Чтобы GitHub выдал OIDC-токен, которым подтверждается право на деплой в Pages
- ( ) Чтобы читать приватные репозитории

`deploy-pages` использует OIDC: короткоживущий токен выдаётся только job-у с `id-token: write`
и подтверждает, что деплой идёт из доверенного workflow этого репозитория.
:::
