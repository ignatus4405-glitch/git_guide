---
title: "Матрицы, кэш, артефакты и секреты"
summary: "Тестирование на нескольких версиях, ускорение сборки кэшем, передача файлов между job-ами через артефакты и безопасная работа с секретами."
order: 2
updated: 2026-10-15
tags: [actions, matrix, cache, artifacts, secrets]
goals:
  - Запускать job в матрице версий и добавлять/исключать комбинации
  - Ускорять прогоны кэшем зависимостей и кэшем сборки
  - Передавать файлы между job-ами через артефакты и читать их из CLI
  - Правильно использовать секреты и переменные окружения
---

## Матрица: одна задача — много окружений

```yaml title=".github/workflows/ci.yml (фрагмент)"
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false            # не отменять остальные комбинации при первой ошибке
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ["3.11", "3.12", "3.13"]
        exclude:
          - os: macos-latest
            python: "3.11"
        include:
          - os: ubuntu-latest
            python: "3.13"
            experimental: true
    continue-on-error: ${{ matrix.experimental || false }}
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: ${{ matrix.python }}
      - run: python3 tools/test_build.py
```

Матрица умножает количество job-ов. Для экономии минут CI:

- сокращайте набор версий до поддерживаемых;
- используйте `include`/`exclude`, чтобы убрать ненужные комбинации;
- тяжёлые проверки оставляйте на одной комбинации, лёгкие — на всей матрице.

## Кэш: экономия минут и времени

```yaml title="Кэш зависимостей"
- uses: actions/cache@v6
  id: pip-cache
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

- run: pip install -r requirements.txt
```

Принцип кэша: **ключ должен зависеть от файла блокировки**. Если ключ постоянный, вы будете
переиспользовать устаревшие зависимости и получите «работает у меня» уже на CI.

::: tip setup-* умеют кэшировать сами
`actions/setup-python`, `setup-node`, `setup-java` принимают `cache: pip` / `cache: npm`.
Это проще и надёжнее собственного `actions/cache`, если язык стандартный.
:::

## Артефакты: передать результат дальше

```yaml title="Загрузка и скачивание"
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - run: python3 build.py
      - uses: actions/upload-artifact@v7
        with:
          name: site-${{ github.sha }}
          path: site/
          retention-days: 14
          if-no-files-found: error

  linkcheck:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/download-artifact@v8
        with:
          name: site-${{ github.sha }}
          path: site
      - run: python3 tools/validate.py --site site
```

Каждый job выполняется на своей чистой машине — переменные и файлы между job-ами не переносятся.
Именно поэтому сборка передаётся артефактом (или кэшем, но семантически это «результат», а не «ускорение»).

```bash title="Работа с артефактами из CLI"
gh run list --limit 5
gh run download <run-id>              # скачать артефакты прогона
gh run view <run-id> --log-failed
```

## Секреты и переменные

```yaml title="Секреты"
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production            # окружение со своими секретами и правилами одобрения
    steps:
      - name: Публикация
        env:
          API_TOKEN: ${{ secrets.API_TOKEN }}      # секрет передаём через env, не в run-строку
          REGION: ${{ vars.DEFAULT_REGION }}       # переменные (не секреты) — из Settings → Variables
        run: ./scripts/deploy.sh --region "$REGION"
```

| Что | Где задаётся | Видно в логах |
| --- | --- | --- |
| `secrets.*` | Settings → Secrets and variables → Actions | нет (маскируется) |
| `vars.*` | там же, Variables | да |
| `GITHUB_TOKEN` | выдаётся автоматически на время прогона | нет |
| Секреты окружения | Settings → Environments | нет |

Правила безопасности:

1. **Не печатайте секреты.** `echo` может раскрыть значение в логах; маскирование работает не всегда (например, после base64).
2. **Не передавайте секреты в PR из форков.** Для внешних PR `secrets.*` пусты, кроме `GITHUB_TOKEN` с правами только на чтение.
3. **Пиньте версии action-ов** (`uses: actions/checkout@v7` — минимум; для критичных — по SHA).
4. **Используйте OIDC** вместо долгоживущих токенов облака: `permissions: id-token: write` и обмен на временные креды.
5. **Проверяйте `pull_request_target`.** Этот триггер даёт права на запись и легко превращается в уязвимость, если в нём запускать код из PR.

::: danger Секрет в логах = утечка
Если секрет попал в лог, он попал и в историю прогонов, доступную всем, кто видит репозиторий.
Немедленно отзовите значение и создайте новое — редактирование логов проблему не решает.
:::

## Итоги

- Матрица запускает одну задачу в разных окружениях; `include`/`exclude` управляют комбинациями.
- Кэш ускоряет прогоны, но должен зависеть от файлов блокировки зависимостей.
- Между job-ами файлы передаются артефактами; каждый job стартует на чистой машине.
- Секреты передаются через `env`, маскируются в логах, в форках недоступны.
- Для облачных провайдеров предпочтителен OIDC вместо статических токенов.

::: exercise Упражнение: ускорить и разделить
1. Добавьте в свой workflow матрицу по двум версиям Python и убедитесь, что создаются два job-а.
2. Включите кэш пип-зависимостей и сравните время второго прогона.
3. Разделите сборку и проверку результата на два job-а, передав результат артефактом.
4. Добавьте секрет в репозиторий (`gh secret set DEMO_TOKEN`) и шаг, который печатает только
   его длину (`${#DEMO_TOKEN}`) — убедитесь, что само значение не попадает в логи.
5. Откройте `gh run view <id> --log-failed` и найдите, как выглядит упавший шаг в логах.
:::

::: quiz Почему секрет, определённый только в `pull_request` из форка, окажется пустым?
- ( ) Потому что форки не могут запускать Actions
- (x) GitHub не передаёт секреты в workflow, запущенные из форков — иначе любой мог бы их украсть
- ( ) Потому что секреты доступны только в job-ах с `needs`

Прогоны из форков получают `GITHUB_TOKEN` с правами только на чтение, а другие секреты
недоступны: код из чужого PR не должен иметь доступ к вашим ключам.
:::
