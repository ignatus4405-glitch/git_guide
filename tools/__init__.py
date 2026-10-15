"""Вспомогательные модули статического генератора курса по Git и GitHub.

Состав:
* ``tools/frontmatter.py`` — минимальный парсер YAML-совместимого front matter.
* ``tools/highlight.py``   — подсветка синтаксиса без внешних зависимостей.
* ``tools/md.py``          — конвертер Markdown → HTML (подмножество GFM + расширения).
* ``tools/content.py``      — модель контента: модули, уроки, страницы, навигация.
* ``tools/templates.py``    — HTML-шаблоны страницы, сайдбара, поиска.
* ``tools/gen_diagrams.py`` — генератор SVG-схем курса (диаграммы как код).
* ``tools/validate.py``     — проверка контента (CI: job "validate").
* ``tools/gen_state.py``    — генерация docs/STATE.md и docs/MANIFEST.json для агентов.
* ``tools/test_build.py``   — самотесты сборки (CI: job "test").
* ``tools/serve.py``        — локальный HTTP-сервер для предпросмотра собранного сайта.
* ``tools/new_lesson.py``   — каркас нового урока (для человека и для агента).
"""

__all__ = ["frontmatter", "highlight", "md", "content", "templates", "gen_diagrams"]
