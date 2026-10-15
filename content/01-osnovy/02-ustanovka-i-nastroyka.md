---
title: "Установка и настройка Git"
summary: "Ставим Git на macOS, Linux и Windows, настраиваем имя, почту, редактор и подключение к GitHub через SSH или токен."
order: 2
updated: 2026-10-15
tags: [git, настройка, ssh, cli]
goals:
  - Установить Git и проверить версию командой git --version
  - Настроить глобальные параметры user.name, user.email, init.defaultBranch и редактор
  - Подключиться к GitHub по SSH и проверить доступ командой ssh -T git@github.com
---

## Установка

```bash title="macOS"
brew install git          # или: xcode-select --install
git --version             # git version 2.4x.x
```

```bash title="Debian / Ubuntu"
sudo apt update && sudo apt install -y git
git --version
```

```bash title="Windows (PowerShell)"
winget install --id Git.Git -e --source winget
# после установки появится «Git Bash» — терминал с привычным набором утилит
git --version
```

::: tip Windows: не путайте Git Bash и WSL
Git Bash — это терминал, который даёт команды unix-типа поверх Windows. WSL — настоящая
Linux-подсистема. Для курса достаточно Git Bash; WSL удобнее, если вы много работаете
с Docker и скриптами.
:::

## Первые три настройки

Git запомнит автора каждого коммита и то, как называть основную ветку. Выполните это один раз:

```bash title="Обязательный минимум"
git config --global user.name "Ваше Имя"
git config --global user.email "you@example.com"    # лучше тот же e-mail, что в GitHub
git config --global init.defaultBranch main
```

`user.email` важнее, чем кажется: именно по нему GitHub связывает коммиты с вашим аккаунтом
и рисует график вклада. Если почта «чужая», коммиты останутся безликими.

Полезные дополнительные настройки:

```bash title="Удобства на каждый день"
git config --global core.editor "code --wait"     # или "nano", "vim"
git config --global pull.rebase true              # pull = fetch + rebase, без лишних merge-коммитов
git config --global push.autoSetupRemote true     # не писать -u origin каждый раз
git config --global rerere.enabled true           # запоминать решения конфликтов
git config --global alias.lg "log --oneline --graph --decorate --all"
```

Проверить, что записалось, и понять, откуда пришло значение:

```bash title="Где что настроено"
git config --list --show-origin
git config --get user.email
```

Файлы настроек читаются в таком порядке (последний побеждает):

| Уровень | Где лежит | Для чего |
| --- | --- | --- |
| `--system` | `/etc/gitconfig` | настройки всей машины |
| `--global` | `~/.gitconfig` | ваши настройки по умолчанию |
| `--local` | `.git/config` в репозитории | настройки одного проекта |

## Подключение к GitHub

У GitHub два основных способа аутентификации. Понимать разницу обязательно: с 2021 года
пароль от аккаунта для `git push` не работает вообще.

::: columns
### SSH-ключ (рекомендуется)

```bash
ssh-keygen -t ed25519 -C "you@example.com"
# Enter, Enter, парольная фраза — по желанию
cat ~/.ssh/id_ed25519.pub        # скопировать содержимое
# GitHub → Settings → SSH and GPG keys → New SSH key
ssh -T git@github.com            # должно ответить: Hi <user>!
```

### Personal Access Token

```bash
# GitHub → Settings → Developer settings →
# Personal access tokens → Fine-grained tokens → Generate
git clone https://github.com/USER/REPO.git
# в качестве пароля — токен; сохранить через менеджер учётных данных
git config --global credential.helper osxkeychain   # macOS
git config --global credential.helper manager       # Windows
git config --global credential.helper "cache --timeout=3600"  # Linux
```
:::

Токен нужен там, где SSH неудобен: в скриптах, CI, контейнерах. Для работы руками SSH-ключ
удобнее: он не истекает по расписанию и не требует копировать секрет в буфер обмена.

::: warning Токен — это пароль
Никогда не вставляйте токен в файлы репозитория, историю команд или в комментарии PR.
GitHub с 2024 года автоматически блокирует push, если находит в коммите строку, похожую
на токен (`push protection`). Подробнее — в модуле «Безопасность и секреты».
:::

## Проверка готовности

```bash title="Чек-лист перед первым уроком"
git --version                  # версия ≥ 2.23 (есть git switch и git restore)
git config --get user.name     # ваше имя
git config --get user.email    # ваша почта
ssh -T git@github.com          # Hi <user>! You've successfully authenticated
gh --version                   # необязательно: GitHub CLI, понадобится в модуле 3
```

Если `git switch` не существует — версия старая: обновите Git, в курсе используются
современные команды вместо `git checkout` там, где это возможно.

## Настройки как код

Настройки `~/.gitconfig` удобно держать в репозитории: тогда новая машина настраивается одной
командой, а изменения проходят ревью, как обычный код.

```bash title="dotfiles-подход"
mkdir -p ~/dotfiles && cd ~/dotfiles
cp ~/.gitconfig gitconfig && git init -q && git add gitconfig
git commit -m "chore: сохранить настройки Git"
# на новой машине:
ln -sf ~/dotfiles/gitconfig ~/.gitconfig
```

Алиасы из `gitconfig` экономят больше всего времени:

```ini title="~/.gitconfig"
[alias]
  s = status --short --branch
  lg = log --oneline --graph --decorate --all
  last = log -1 --stat
  undo = reset --soft HEAD~1
  amend = commit --amend --no-edit
  who = blame -w -C -L
```

## Проверка на чужой машине

Если вы работаете за чужим компьютером или в контейнере, помните: Git читает настройки из
домашнего каталога, а ключи обычно не переносятся. Быстрая проверка перед началом работы
и локальные настройки только для конкретного репозитория:

```bash title="Локальные настройки в проекте"
git config user.email "work@company.com"     # без --global: действует в этом репозитории
git config --list --show-origin | head -20   # понять, какие файлы настроек применены
git config --global --unset user.email       # убрать лишнее
```

::: warning Не отключайте проверки «чтобы работало»
Частая ошибка на новой машине — `git config --global core.autocrlf true` «потому что Windows».
Если проект уже использует `.gitattributes`, такая настройка создаёт ложные изменения в каждом файле.
Правильный порядок: сначала посмотрите, что требует проект (`CONTRIBUTING.md`), потом настраивайте.
:::

## Итоги

- Установка Git — одна команда в вашей системе; проверка — `git --version`.
- Три глобальные настройки обязательны: имя, почта, `init.defaultBranch`.
- Для GitHub используем SSH-ключ (ручная работа) или fine-grained токен (автоматизация).
- Проверка доступа: `ssh -T git@github.com` и `gh auth status`.

::: exercise Упражнение: настроить окружение
1. Установите Git и проверьте версию.
2. Задайте `user.name`, `user.email`, `init.defaultBranch main` и `pull.rebase true`.
3. Сгенерируйте SSH-ключ, добавьте публичную часть в GitHub и добейтесь ответа `Hi <user>!`
   от `ssh -T git@github.com`.
4. Выполните `git config --list --show-origin` и объясните, какое значение откуда пришло.
:::

::: quiz Что произойдёт, если запушить с паролем аккаунта вместо токена или SSH-ключа?
- ( ) Коммит отправится, но автор будет неверным
- (x) Аутентификация не пройдёт: GitHub требует токен или ключ
- ( ) GitHub принудительно включит двухфакторную аутентификацию

С 2021 года пароли аккаунта не принимаются для операций Git по HTTPS. Нужен personal access
token (или fine-grained token) либо SSH-ключ; при включённой 2FA это требование не меняется.
:::
