---
title: "GitHub Flow и gh CLI"
summary: "Модель ветвления GitHub Flow, защита веток и правила слияния, а также GitHub CLI — все действия GitHub из терминала."
order: 3
updated: 2026-10-15
tags: [github, gh-cli, branch-protection, flow]
goals:
  - Описать модель GitHub Flow и объяснить, почему main всегда готова к релизу
  - Настроить защиту ветки main: обязательное ревью, статусы проверок, запрет force-push
  - Выполнять типовые операции GitHub через gh CLI: репозитории, PR, issues, релизы
---

## GitHub Flow за шесть шагов

GitHub Flow — самая простая рабочая модель, и она подходит большинству команд:

1. `main` всегда в рабочем состоянии и готова к деплою.
2. Под задачу создаётся ветка с говорящим именем.
3. В ветку идут коммиты; ветка регулярно пушится.
4. Как только работа готова — открывается Pull Request.
5. В PR проходят обсуждение, ревью и автоматические проверки.
6. После слияния изменения деплоятся, ветка удаляется.

```bash title="Цикл целиком"
git switch -c feat/onboarding-checklist
# …правки…
git push -u origin feat/onboarding-checklist
gh pr create --fill              # заголовок и описание из коммитов
gh pr checks --watch             # ждать окончания проверок
gh pr merge --squash --delete-branch
git switch main && git pull --rebase
```

::: info Имена ветвей как метаданные
Договоритесь о префиксах: `feat/`, `fix/`, `docs/`, `chore/`, `hotfix/`. По ним работают
фильтры в списке веток, автоматизация в Actions и понятно, что происходит без открытия PR.
:::

## Защита ветки main

Правила включаются в настройках репозитория: **Settings → Branches → Add branch protection rule**.
Для публичного проекта минимальный разумный набор такой:

| Правило | Зачем |
| --- | --- |
| Require a pull request before merging | в `main` нельзя пушить напрямую |
| Require approvals (1+) | хотя бы один человек посмотрел изменения |
| Dismiss stale approvals on new commits | старый апрув не действует после новых правок |
| Require status checks to pass | CI должен быть зелёным |
| Require conversation resolution | все замечания закрыты явно |
| Require linear history | запрет merge-коммитов, только squash/rebase |
| Do not allow bypassing | правила действуют и для администраторов |
| Restrict force pushes | защита от перезаписи истории |

Через API и CLI это тоже настраивается:

```bash title="Включить правило (требуются права admin)"
gh api -X PUT repos/OWNER/REPO/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -f "required_pull_request_reviews[required_approving_review_count]=1" \
  -f "required_status_checks[strict]=true" \
  -f 'required_status_checks[contexts][]=validate' \
  -f "enforce_admins=true" \
  -f "allow_force_pushes=false" \
  -f "required_linear_history=true"
```

::: tip Статусы проверок
Название в `contexts` должно точно совпадать с именем job в workflow (или с именем workflow).
Посмотрите список доступных проверок: `gh api repos/OWNER/REPO/commits/main/check-runs --jq '.check_runs[].name'`.
:::

## GitHub CLI: зачем он нужен

`gh` — официальный клиент GitHub для терминала. Он избавляет от переключения в браузер
и, что важнее, делает операции воспроизводимыми и автоматизируемыми (в CI тоже используется).

```bash title="Установка и вход"
brew install gh          # macOS; на других системах — см. cli.github.com
gh auth login            # интерактивно: GitHub.com → HTTPS/SSH → браузер или токен
gh auth status           # что настроено, какие права у токена
gh auth refresh -s workflow,project   # добавить права (scopes)
```

```bash title="Повседневные команды"
gh repo create my-project --public --source=. --remote=origin   # создать из локального каталога
gh repo clone OWNER/REPO                                        # клонировать
gh repo fork --clone --remote                                  # форк + локальный клон

gh issue list --label bug --state open
gh issue create --title "Баг: пустой ответ" --body "Шаги воспроизведения…"
gh issue close 12 --reason completed

gh pr list --author "@me"
gh pr create --fill --draft
gh pr review --approve --body "LGTM: проверено локально"
gh pr checkout 42                    # переключиться на ветку PR локально
gh pr merge 42 --rebase --delete-branch

gh run list --limit 5                # последние прогоны Actions
gh run watch                         # смотреть текущий прогон
gh release create v1.2.0 --generate-notes
```

::: note Работа с API напрямую
Всё, чего нет в `gh`, доступно через `gh api`: например,
`gh api repos/OWNER/REPO/branches/main/protection --jq '.required_status_checks'`
или `gh api graphql -f query='{ viewer { login } }'`. Так удобно проверять состояние репозитория в скриптах.
:::

## Что выбрать: веб или CLI

| Задача | Удобнее |
| --- | --- |
| Прочитать дифф и обсудить построчно | веб-интерфейс |
| Массовые операции, фильтры, скрипты | `gh` + `gh api` |
| Создать PR с описанием из шаблона | `gh pr create --fill` |
| Посмотреть логи прогона Actions | `gh run view --log-failed` |
| Настройки репозитория и правила веток | веб (нагляднее) или `gh api` |

## Итоги

- GitHub Flow: `main` готова к деплою, задача — в ветке, изменения — через PR.
- Защита ветки делает правила формальными: без ревью и зелёных проверок в `main` не попасть.
- `gh` покрывает почти весь ежедневный сценарий и легко встраивается в скрипты и CI.
- Все настройки доступны через API — значит, их можно описать кодом и ревьюить.

::: exercise Упражнение: терминал вместо браузера
1. Создайте репозиторий через `gh repo create`, клонируйте его, добавьте README и запушьте.
2. Создайте issue с меткой `bug` и ветку `fix/...` из созданной задачи.
3. Сделайте коммит, запушьте ветку и создайте PR со ссылкой `Closes #<номер>`, используя `--fill`.
4. Посмотрите прогон проверок (`gh run list`, `gh pr checks`), слейте PR и убедитесь,
   что issue закрылся автоматически.
:::

::: quiz Команда `gh pr checks --watch` закончилась ошибкой, но изменения нужны срочно. Что делать?
- ( ) Влить PR через --admin: время дороже
- (x) Посмотреть упавший job (`gh run view --log-failed`), починить причину и запушить правку
- ( ) Отключить защиту ветки и запушить в main напрямую

Красные проверки означают, что с изменениями что-то не так: либо код, либо конфигурация CI.
Разбор логов занимает минуты, а обход правил ломает доверие к процессу и обычно приводит
к откату изменений.
:::
