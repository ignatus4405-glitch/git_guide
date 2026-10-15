---
title: "Хуки, шаблоны и .gitattributes"
summary: "Локальные и серверные хуки, управляемые через pre-commit, шаблоны commit message, .gitattributes и выравнивание переводов строк между ОС."
order: 1
updated: 2026-10-15
tags: [hooks, pre-commit, gitattributes, качество]
goals:
  - Понимать, какие хуки есть в Git и чем клиентские отличаются от серверных
  - Настроить pre-commit с линтерами и проверками, работающими до коммита
  - Использовать .gitattributes для переводов строк, diff-драйверов и архивов
---

## Зачем нужны хуки

Хук — это скрипт, который Git запускает перед или после события: коммита, push, merge.
Клиентские хуки живут в `.git/hooks/` **и не попадают в репозиторий** — поэтому их
обычно оформляют через менеджеры (pre-commit, husky, lefthook), которые устанавливают
скрипты всем разработчикам.

| Хук | Когда срабатывает | Типовое применение |
| --- | --- | --- |
| `pre-commit` | перед созданием коммита | линтеры, форматирование, поиск секретов |
| `commit-msg` | после ввода сообщения | проверка формата (Conventional Commits) |
| `pre-push` | перед отправкой | тесты, сборка |
| `post-checkout`, `post-merge` | после переключения/слияния | переустановка зависимостей |
| `pre-receive` (серверный) | при получении push | политики: запрет секретов, размера, авторов |

## Правило: быстрые проверки локально, полные — в CI

Локальные хуки должны выполняться за секунды. Если `pre-commit` запускает полный набор тестов,
разработчики начнут коммитить с `--no-verify` и перестанут доверять проверкам.

```text title="Распределение проверок"
pre-commit   : форматирование, линтер по изменённым файлам, поиск секретов   (< 5 с)
pre-push     : тесты модуля, затронутого изменениями                          (< 60 с)
CI           : полный набор тестов, матрица версий, сборка, проверка ссылок
```

## pre-commit: управляемые хуки, попадающие в репозиторий

```yaml title=".pre-commit-config.yaml"
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ["--maxkb=1024"]
      - id: mixed-line-ending
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.17.1
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks        # ищет секреты по шаблонам
```

```bash title="Установка и использование"
pipx install pre-commit
pre-commit install                # пропишет хук в .git/hooks/pre-commit
pre-commit run --all-files        # прогнать по всему репозиторию
pre-commit autoupdate             # обновить версии хуков
pre-commit run --hook-stage push --all-files
```

::: tip Как заставить хуки работать у всех
Сам `.git/hooks` в репозиторий не попадает. Решения два: **pre-commit/husky** (устанавливаются
одной командой, документируются в README) или `core.hooksPath` в репозитории:

```bash
git config core.hooksPath .githooks
```

Второй вариант проще, но требует, чтобы каждый разработчик выполнил эту команду: напишите её
в `CONTRIBUTING.md` и в скрипте первичной настройки.
:::

## commit-msg: формат сообщений

```bash title=".githooks/commit-msg"
#!/bin/sh
MSG_FILE="$1"
PATTERN='^(feat|fix|docs|refactor|test|chore|build|perf)(\([a-z0-9-]+\))?: .{5,72}$'
if ! head -n1 "$MSG_FILE" | grep -Eq "$PATTERN"; then
  echo "Сообщение должно соответствовать Conventional Commits:"
  echo "  feat(scope): краткое описание"
  head -n1 "$MSG_FILE"
  exit 1
fi
```

Такой хук заставляет писать осмысленные сообщения и упрощает автоматическую сборку changelog.

## .gitattributes: одна строка — меньше проблем

```text title=".gitattributes"
# Всегда LF в репозитории, для Windows — CRLF в рабочей копии
* text=auto eol=lf
*.bat text eol=crlf
*.ps1 text eol=crlf

# Бинарные файлы не «текстовые»: Git не будет пытаться их сливать
*.png binary
*.jpg binary
*.pdf binary
*.xlsx binary

# Языки, для которых GitHub покажет подсветку и статистику
*.md      linguist-documentation
docs/*    linguist-documentation

# Файлы генераторов не считаем в статистике языка
site/*    linguist-generated=true

# Мержим lock-файлы всегда «нашим» вариантом и пересобираем
package-lock.json merge=binary
```

Практическая проблема, которую решает первая строка: на Windows редакторы по умолчанию
пишут CRLF, Git это фиксирует, и весь файл выглядит изменённым. `text=auto eol=lf` убирает
такие диффы из ревью.

## Ещё две мелочи: шаблон коммита и git worktree

```bash title="Шаблон сообщения коммита"
git config --global commit.template ~/.gitmessage
cat > ~/.gitmessage <<'EOF'
# <тип>(область): краткое описание до 72 символов
#
# Зачем это изменение? Что проверено?
# Closes #
EOF
```

```bash title="Несколько рабочих каталогов на одной истории"
git worktree add ../repo-hotfix hotfix/1.2.1   # отдельный каталог для срочной правки
git worktree list
git worktree remove ../repo-hotfix
```

`worktree` заменяет «отложу правки в stash и переключусь»: вы работаете в двух каталогах
одновременно, не теряя контекст и не откладывая изменения.

## Итоги

- Хуки автоматизируют проверки, но клиентские не версионируются — их устанавливают через pre-commit или `core.hooksPath`.
- Локальные проверки должны быть быстрыми; полный набор тестов — на CI.
- `commit-msg` поддерживает единый формат сообщений и автоматический changelog.
- `.gitattributes` решает переводы строк, бинарные файлы и статистику языков.
- `git worktree` даёт несколько рабочих каталогов на одну историю.

::: exercise Упражнение: настроить локальные проверки
1. Установите `pre-commit`, добавьте конфигурацию из урока и выполните `pre-commit run --all-files`.
2. Создайте файл с «неправильным» yaml и убедитесь, что хук блокирует коммит.
3. Добавьте `.githooks/commit-msg` и включите `core.hooksPath`; попробуйте закоммитить
   сообщение `fix` — коммит должен быть отклонён.
4. Добавьте `.gitattributes` в проект и убедитесь, что бинарные файлы больше не считаются текстом.
5. Сделайте `git worktree add ../hotfix worktree-test` и покажите, что `git worktree list` видит оба каталога.
:::

::: quiz Почему `.git/hooks/pre-commit` не работает у коллеги после клонирования?
- ( ) Git блокирует хуки в свежих клонах
- (x) Каталог .git не клонируется: хуки нужно устанавливать в каждом рабочем каталоге
- ( ) Хуки работают только при наличии прав на push

`.git/` — локальное хранилище, оно не входит в клонируемые данные. Поэтому хуки оформляют
через pre-commit/husky или `core.hooksPath`, чтобы установка была одной командой.
:::
