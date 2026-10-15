# GitHub: полный практический курс для Windows

Небольшое офлайн-приложение на русском языке, которое шаг за шагом объясняет Git и GitHub — от установки Git до Pull Requests, GitHub Actions и безопасных релизов.

## Что внутри

- 21 последовательный урок с конкретными командами, пояснениями, практическим заданием и контрольным вопросом.
- Встроенные интерактивные схемы для каждого урока: Git-процесс, ветки, PR, Actions, релиз и другие темы. Схемы рисуются самим приложением и работают без интернета.
- Поиск по урокам, навигация по разделам и индикатор выполнения курса.
- Локальное сохранение прогресса в `%LOCALAPPDATA%\GitHubCourse\progress.json`.
- Самодостаточная сборка для Windows x64, которую создаёт GitHub Actions.

Курс посвящён и Git — программе контроля версий, и GitHub — платформе для удалённых репозиториев и командной работы. Приложение не запрашивает аккаунт, пароль или токены и не отправляет прогресс в сеть.

## Скачать готовую Windows-сборку

1. Откройте в репозитории вкладку **Actions**.
2. Выберите успешный запуск **Validate course and build Windows app**.
3. Внизу страницы скачайте артефакт **GitHubCourse-Windows-x64**.
4. Распакуйте ZIP и запустите `GitHubCourse.exe`.

Workflow автоматически запускается при push, Pull Request или вручную через **Run workflow**. Артефакт сохраняется в запуске Actions на 14 дней. Это ZIP с self-contained Windows x64-приложением; отдельно устанавливать .NET на целевом компьютере не требуется.

Приложение пока не подписано цифровым сертификатом издателя, поэтому Windows может показать предупреждение SmartScreen. Скачивайте его только из доверенного запуска Actions этого репозитория и проверяйте источник.

## Разработка и сборка

Требуются Windows, .NET 8 SDK и Python 3. Запустите команды из корня репозитория:

```powershell
python -m unittest discover -s tests -v
python scripts/validate_course.py
dotnet publish src/GitHubCourse/GitHubCourse.csproj `
  --configuration Release `
  --runtime win-x64 `
  --self-contained true `
  -p:PublishSingleFile=true `
  -p:IncludeNativeLibrariesForSelfExtract=true `
  -p:EnableCompressionInSingleFile=true `
  --output artifacts/GitHubCourse-win-x64
```

Готовое приложение будет в `artifacts/GitHubCourse-win-x64/`. Workflow GitHub Actions выполняет проверку данных на Ubuntu, сборку WPF-приложения на Windows и прикладывает ZIP к запуску.

## Где что находится

```text
.github/workflows/build-windows.yml  Проверка контента и автосборка Windows
Course/lessons.json                  Уроки, команды, схемы, практика и вопросы
src/GitHubCourse/                    WPF-приложение Windows
scripts/validate_course.py           Проверка структуры курса
tests/test_course_content.py          Автотесты содержания курса
AGENTS.md                            Инструкция следующему агенту
CHANGELOG.md                         Журнал изменений
CONTRIBUTING.md                      Как добавлять уроки и менять проект
docs/ARCHITECTURE.md                 Архитектура приложения
docs/PROJECT_STATE.md                Состояние проекта и точки продолжения
```

## Документация и продолжение работы

Перед изменениями прочитайте `AGENTS.md`, `docs/PROJECT_STATE.md` и `docs/ARCHITECTURE.md`. Новые уроки добавляйте в `Course/lessons.json`, а не в код интерфейса; схема данных и правила проверки описаны в `CONTRIBUTING.md`. Каждое заметное изменение фиксируйте в `CHANGELOG.md`. На каждый push GitHub Actions повторно проверит курс и запустит сборку Windows-приложения.
