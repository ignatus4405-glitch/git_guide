# Состояние проекта и передача следующему агенту

## Кратко

Первая версия офлайн-приложения для изучения Git и GitHub на Windows реализована в этой ветке. Основной продукт — WPF/.NET 8 приложение, исходники курса — `Course/lessons.json`, Windows ZIP собирается GitHub Actions. На дату первичной реализации: локальные Python-валидация и тесты проходят; подтверждение Windows-компиляции ожидается от CI после push.

## Готово

- [x] Русскоязычное WPF-окно, sidebar с разделами и уроками, поиск, навигация вперёд/назад.
- [x] 21 урок: основы, установка Git, репозитории, ветки, синхронизация, PR/review, конфликты, отмена, Issues/Projects, Actions, Releases, fork, безопасность и GitHub CLI.
- [x] В каждом уроке есть визуальная схема, практика и интерактивный тест с объяснением.
- [x] Прогресс сохраняется локально и переживает перезапуск приложения.
- [x] Проверка структуры содержания и Python unit tests.
- [x] Workflow GitHub Actions: Ubuntu content checks → Windows x64 self-contained publish → ZIP artifact.
- [x] README, руководство агенту, авторинг и архитектурная документация.

## Проверки и следующие шаги

1. Запустить `python -m unittest discover -s tests -v` и `python scripts/validate_course.py` после изменений содержания.
2. После отправки кода проверить Actions: workflow **Validate course and build Windows app**, jobs `validate-course` и `build-windows` должны быть зелёными. При ошибке в C#/XAML откройте первый упавший шаг и исправьте сборку; не считать программу готовой к скачиванию до успешного Windows job.
3. Для визуальной проверки Windows-запуска скачайте созданный артефакт, распакуйте и пройдите несколько уроков, проверьте поиск, тест, навигацию и сохранение прогресса после перезапуска.
4. Если сборка прошла, но название артефакта/пути изменено, синхронизируйте README, `AGENTS.md` и `CONTRIBUTING.md`.
5. Для публичного выпуска создайте отдельный GitHub Release только после проверки exe на Windows; текущая Actions-сборка — временный артефакт, который хранится 14 дней.

## Где продолжать

- Новые или исправляемые уроки: `Course/lessons.json`.
- UI и поведение: `src/GitHubCourse/MainWindow.xaml`, `MainWindow.xaml.cs`.
- Модели и сохранение: `src/GitHubCourse/Models/`, `src/GitHubCourse/Services/`.
- Сборка: `.github/workflows/build-windows.yml`.
- Процедура работы: `AGENTS.md`, `CONTRIBUTING.md`.

Все пользовательские изменения и выполненные проверки записываются в `CHANGELOG.md`.
