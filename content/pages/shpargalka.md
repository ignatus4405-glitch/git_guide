---
title: "Шпаргалка по Git и GitHub"
summary: "Все команды курса в одном месте: настройка, коммиты, ветки, история, отмена, удалённые репозитории, Actions и оформление репозитория."
order: 2
updated: 2026-10-15
icon: "🧾"
nav_title: "Шпаргалка команд"
---

## Настройка окружения

```bash title="Первые шаги"
git --version
git config --global user.name "Ваше Имя"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global rerere.enabled true
ssh-keygen -t ed25519 -C "you@example.com" && ssh -T git@github.com
gh auth login && gh auth status
```

## Основной цикл

```bash title="Повседневные команды"
git status                     # что происходит
git diff                       # правки рабочей копии
git diff --staged              # что уйдёт в коммит
git add -p                     # добавить изменения частями
git commit -m "feat: смысл"    # зафиксировать
git push                       # опубликовать
```

## Работа с ветками и историей

```bash title="Ветки и слияния"
git switch -c feat/name        # создать ветку и переключиться
git switch main                # переключиться
git branch -vv                 # ветки и их upstream
git merge --no-ff feat/name    # слияние с merge-коммитом
git merge --abort              # отменить слияние
git branch -d feat/name        # удалить слитую ветку
```

```bash title="История"
git log --oneline --graph --decorate --all
git log --author="Анна" --since="2 weeks ago"
git log -S "DATABASE_URL" --oneline
git log --follow -- README.md
git blame -L 40,60 build.py
git show HEAD
```

## Отмена изменений

```bash title="Четыре уровня"
git restore file.py             # вернуть файл из индекса/HEAD
git restore --staged file.py    # убрать из индекса
git commit --amend              # поправить последний коммит
git reset --soft HEAD~1         # убрать коммит, оставив изменения
git reset --hard HEAD~1         # уничтожить коммит и правки (!)
git revert <sha>                # безопасная отмена для общих ветвей
git reflog                      # найти потерянные коммиты
git stash push -m "черновик"    # отложить правки
git stash pop
```

## Rebase и чистка истории

```bash title="Аккуратный PR"
git fetch origin && git rebase origin/main
git rebase -i HEAD~3            # squash/reword/drop
git rebase --continue | --skip | --abort
git cherry-pick <sha>
git push --force-with-lease     # только для своих ветвей
```

## Удалённые репозитории

```bash title="Синхронизация"
git remote -v
git remote add upstream git@github.com:OWNER/REPO.git
git fetch origin
git pull --rebase
git push -u origin feat/name
git push -d origin feat/old
git remote set-url origin git@github-work:company/repo.git
```

## GitHub CLI

```bash title="gh: репозитории, PR, issues, релизы"
gh repo create my-app --public --source=. --remote=origin --push
gh repo fork --clone --remote
gh pr create --fill --draft
gh pr checks --watch
gh pr review --approve --body "Проверено локально"
gh pr merge 42 --squash --delete-branch
gh issue create --title "Баг" --label bug
gh issue develop 42 --checkout
gh run list && gh run watch && gh run view --log-failed
gh release create v1.0.0 --generate-notes
gh secret set TOKEN --body "$(openssl rand -hex 24)"
```

## Git Actions: минимум для CI

```yaml title=".github/workflows/ci.yml"
name: CI
on: [push, pull_request]
permissions:
  contents: read
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with: {python-version: "3.12"}
      - run: python3 tools/test_build.py
```

## Публикация на Pages

```yaml title=".github/workflows/pages.yml (ядро)"
permissions: {contents: read, pages: write, id-token: write}
jobs:
  build:
    runs-on: ubuntu-latest
    steps: [checkout, build, actions/upload-pages-artifact@v5]
  deploy:
    needs: build
    environment: {name: github-pages, url: "${{ steps.deployment.outputs.page_url }}"}
    steps: [{uses: actions/deploy-pages@v5, id: deployment}]
```

## Оформление репозитория

```text title="Полезные файлы"
.github/workflows/*.yml          # CI/CD
.github/ISSUE_TEMPLATE/*.md      # шаблоны задач
.github/PULL_REQUEST_TEMPLATE.md # описание PR
.github/CODEOWNERS               # кто ревьюит какие пути
.github/dependabot.yml           # обновления зависимостей
.gitignore                       # что не коммитить
.gitattributes                   # переводы строк, бинарные файлы, LFS
CONTRIBUTING.md                  # как участвовать
CHANGELOG.md                     # история версий
```

## Диагностика: что смотреть при проблеме

| Проблема | Команды |
| --- | --- |
| Не понимаю состояние | `git status`, `git log --oneline --graph --all` |
| Push отклонён | `git fetch`, `git log HEAD..origin/main`, `git pull --rebase` |
| Конфликт | `git status`, `git diff --diff-filter=U`, `git checkout --ours/--theirs`, `git merge --abort` |
| Потерял коммит | `git reflog`, `git switch -c rescue <sha>` |
| Секрет в истории | `git log -p -S "ключ"`, `git filter-repo`, отзыв ключа |
| Тяжёлый репозиторий | `git count-objects -vH`, `git verify-pack -v`, `git lfs track` |
| Битый репозиторий | `git fsck --full`, `git fsck --lost-found` |
| Не запускается workflow | `gh run list`, `gh run view <id> --log-failed`, проверить YAML |

::: tip Как пользоваться шпаргалкой
Не пытайтесь запомнить команды — запомните уровни: рабочая копия, индекс, локальная история,
публичная история. На каждом уровне есть свой инструмент отмены, а всё остальное — детали.
:::
