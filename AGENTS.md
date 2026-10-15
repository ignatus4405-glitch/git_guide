# Инструкция агентам и сопровождающим

Этот файл — краткая точка входа для следующего агента, который продолжит работу с репозиторием.

## Прежде чем менять код

1. Прочитайте `README.md`, `docs/PROJECT_STATE.md`, `docs/ARCHITECTURE.md` и последние записи `CHANGELOG.md`.
2. Проверьте `git status` и сохраняйте существующие изменения пользователя.
3. Работайте в текущей ветке сессии; не переключайтесь на другую ветку.
4. Основной язык продукта и документации — русский. Оставляйте распространённые Git-команды и названия GitHub на английском.

## Проект в одном абзаце

Это офлайн WPF-приложение для Windows x64 на .NET 8. Текст курса и данные схем живут в `Course/lessons.json`; интерфейс строится из этих данных. Прогресс хранится локально в `%LOCALAPPDATA%\GitHubCourse\progress.json`. GitHub Actions сначала проверяет контент и тесты на Ubuntu, а затем публикует self-contained Windows x64 ZIP на Windows runner.

## Обязательная проверка изменений

После изменения курса или Python-проверок запустите из корня репозитория:

```powershell
python -m unittest discover -s tests -v
python scripts/validate_course.py
```

После изменения C# или XAML проверьте обе команды выше и соберите приложение на Windows с .NET 8:

```powershell
dotnet publish src/GitHubCourse/GitHubCourse.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:EnableCompressionInSingleFile=true -o artifacts/GitHubCourse-win-x64
```

Windows-сборка выполняется GitHub Actions на каждом push/PR. Просмотрите первый упавший шаг в Actions; не сообщайте о готовой сборке до успешного результата Windows job.

## Документируйте каждую задачу

- Добавьте запись в `CHANGELOG.md` при каждом пользовательском изменении: что добавлено/исправлено и какие проверки запускались.
- Если изменились структура проекта, команды сборки или план следующей работы, обновите `docs/ARCHITECTURE.md` и/или `docs/PROJECT_STATE.md`.
- Обновляйте README, если пользовательские шаги запуска или получения сборки изменились.
- Не включайте `bin/`, `obj/`, `artifacts/`, токены, персональные секреты и реальные ключи в Git.

## Как продолжить

- Добавить урок: отредактировать JSON и контрольные тесты; следовать `CONTRIBUTING.md`.
- Изменить вид или поведение: `src/GitHubCourse/MainWindow.xaml` и `MainWindow.xaml.cs`.
- Изменить хранение прогресса или загрузку курса: `src/GitHubCourse/Services/`.
- Поменять автоматическую сборку: `.github/workflows/build-windows.yml`.
- Сделать следующую версию: сначала убедиться, что Actions зелёный, затем подготовить тег/Release по уроку 17.
