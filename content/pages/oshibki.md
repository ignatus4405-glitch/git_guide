---
title: "20 типичных ошибок и как их исправить"
summary: "Разбор частых проблем: от «push отклонён» и конфликтов до утечки секретов и сломанного workflow — с точными командами решения."
order: 4
updated: 2026-10-15
icon: "🚑"
nav_title: "Ошибки и решения"
---

## Рабочая копия и коммиты

### 1. «Я закоммитил лишний файл»

```bash
git rm --cached secret.env          # убрать из индекса, файл останется на диске
echo "secret.env" >> .gitignore
git commit --amend --no-edit        # если коммит ещё не отправлен
```

Если коммит уже отправлен — `git rm` + новый коммит: файл останется в истории, но исчезнет
из текущего состояния. Если в файле был секрет — сначала отзовите значение.

### 2. «Забыл добавить файл в коммит»

```bash
git add forgotten.py
git commit --amend --no-edit        # только для последнего, ещё не отправленного коммита
```

### 3. «Сообщение коммита с опечаткой»

```bash
git commit --amend -m "fix: правильное сообщение"   # только для последнего коммита
git rebase -i HEAD~3                                 # reword для более старых
```

### 4. «Случайно удалил файл и закоммитил»

```bash
git restore --source=HEAD~1 path/to/file.py    # вернуть из предыдущего коммита
git log --diff-filter=D --name-only --oneline  # найти, где файл удалён
git revert <sha>                               # если удаление уже опубликовано
```

### 5. «Коммиты попали не в ту ветку»

```bash
git switch правильная-ветка
git cherry-pick <sha>              # перенести нужные коммиты
git switch неправильная-ветка
git reset --hard HEAD~1            # убрать их оттуда (если не опубликованы)
```

## История и отмена

### 6. «Сделал reset --hard и потерял работу»

```bash
git reflog                          # найдите SHA состояния до reset
git switch -c rescue <sha>          # восстановите в новую ветку
```

Потерянное сохраняется в reflog ещё ~30 дней (зависит от `gc.reflogExpire`), поэтому паниковать рано.

### 7. «Случайно сделал rebase общей ветки»

```bash
git reflog                          # найти исходный коммит ветки
git reset --hard <sha-до-rebase>
git push --force-with-lease         # вернуть ветку к прежнему состоянию
# затем предупредите команду: у всех остались другие SHA
```

### 8. «Хочу отменить merge»

```bash
git merge --abort                   # если merge в процессе
git revert -m 1 <merge-sha>         # если merge уже закоммичен и отправлен
```

### 9. «Конфликт, и я не понимаю, что теряю»

```bash
git checkout --merge <файл>         # вернуть маркеры конфликта, если уже «исправили»
git diff --diff-filter=U            # посмотреть только конфликтующие файлы
git log --merge --oneline           # коммиты обеих сторон
git merge --abort                   # отступить и пересмотреть подход
```

### 10. «Ветка разошлась, push не проходит»

```bash
git fetch origin
git log --oneline HEAD..origin/main     # что у вас нет
git pull --rebase origin main           # или merge, если ветка общая
git push
```

## Удалённые репозитории

### 11. «Не могу запушить: Permission denied (publickey)»

```bash
ssh -T git@github.com                   # какая связка ключей отвечает
ssh-add -l                              # загружен ли ключ в агент
ssh-add ~/.ssh/id_ed25519
git remote -v                            # HTTPS или SSH адрес?
git remote set-url origin git@github.com:USER/REPO.git
```

### 12. «Отправил неправильный force-push»

Остановитесь и сделайте два шага: получите актуальную локальную копию
(`git fetch origin`) и сообщите команде. Восстановление возможно из reflog того человека,
у которого остались прежние коммиты: `git push --force-with-lease origin <sha>:main`.

### 13. «Не могу удалить ветку»

```bash
git branch -d feature/old       # откажется, если ветка не слита
git branch -D feature/old       # принудительно (коммиты потеряются)
git push -d origin feature/old  # удалить на сервере
```

### 14. «Форк отстал от upstream»

```bash
git remote add upstream https://github.com/OWNER/REPO.git
git fetch upstream
git switch main && git rebase upstream/main
git push --force-with-lease origin main
```

## Файлы и репозиторий

### 15. «В репозиторий попал большой файл»

```bash
git rm --cached big.iso          # убрать из текущего состояния
git lfs track "*.iso"            # или вынести в LFS
git filter-repo --invert-paths --path big.iso   # удалить из истории (зеркальная копия!)
```

### 16. «Весь файл показан как изменённый (переводы строк)»

```bash
echo "* text=auto eol=lf" >> .gitattributes
git add --renormalize .
git commit -m "chore: нормализовать переводы строк"
```

### 17. «.gitignore не работает»

Файл уже отслеживается — игнор на такие файлы не действует. Проверьте и исправьте:

```bash
git check-ignore -v path/to/file     # какое правило сработало
git ls-files --error-unmatch file    # отслеживается ли файл
git rm --cached file                 # перестать отслеживать
```

### 18. «Подмодуль пустой после клонирования»

```bash
git submodule update --init --recursive
# или клонируйте сразу правильно:
git clone --recurse-submodules <url>
```

## GitHub Actions и безопасность

### 19. «Workflow не запускается»

Проверьте по порядку:

- файл лежит именно в `.github/workflows/` (регистр важен);
- YAML валиден: отступы, отсутствие табов (`python3 -c "import yaml,sys;yaml.safe_load(open('.github/workflows/ci.yml'))"`);
- триггер соответствует событию: `on: push` для ветки, где вы пушите;
- workflow включён в интерфейсе (Settings → Actions → General);
- для PR из форка нет секретов — это не ошибка, а защита.

### 20. «Секрет попал в репозиторий или в лог CI»

1. **Отозвать** значение у провайдера и выпустить новое.
2. Обновить секреты: `gh secret set NAME --body "новое"`.
3. Убрать значение из файла и истории (`git filter-repo --replace-text`).
4. Включить `push protection` и `secret scanning`.
5. Добавить проверку в pre-commit или workflow, чтобы это не повторилось.

::: danger Общее правило
Прежде чем выполнять `reset --hard`, `--force`, `filter-repo` или удалять ветку,
сделайте дешёвую страховку: `git branch backup/$(date +%s)`. Ветка-бэкап занимает 41 байт
и спасает часы работы.
:::

::: tip Про «а что, если...»
Если вы не уверены, что произойдёт от команды, — проверьте её в учебном репозитории.
В Git почти все операции обратимы: коммиты не удаляются сразу, а ссылки можно вернуть
через `reflog`.
:::
