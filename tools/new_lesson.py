#!/usr/bin/env python3
"""Каркас нового урока: создаёт файл с front matter и структурой по стандарту курса.

Запуск::

    python3 tools/new_lesson.py --module git-osnovy --order 7 --title "Теги и релизы"
    python3 tools/new_lesson.py --list                 # показать модули
    python3 tools/new_lesson.py --page "Как учиться"   # отдельная страница

Скрипт не перезаписывает существующие файлы и печатает подсказку, что делать дальше
(заполнить теорию, добавить схему, запустить сборку и валидацию).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build import ROOT, load_config  # noqa: E402
from tools.content import load_site  # noqa: E402


def slugify(title: str) -> str:
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
        "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
        "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    out = []
    for ch in title.lower():
        if ch in table:
            out.append(table[ch])
        elif ch.isalnum() and ch.isascii():
            out.append(ch)
        elif ch in " \t-—":
            out.append("-")
    return re.sub(r"-{2,}", "-", "".join(out)).strip("-") or "novyy-urok"


LESSON_TEMPLATE = """---
title: "{title}"
summary: "Короткое описание урока в 2–3 строках: что ученик поймёт и почему это важно."
order: {order}
updated: {today}
tags: [git]
goals:
  - Первый измеримый результат урока
  - Второй измеримый результат урока
---

Вводный абзац: зачем этот материал и какие задачи он решает.

![Схема: подпись](assets/img/diagrams/three-trees.svg "Краткая подпись схемы")

## Первый раздел

Объяснение с опорой на схему выше.

```bash title="Пример команды"
git status
```

::: note Заметка
Дополнительный контекст: типичная путаница, историческая справка, ссылка на команду.
:::

## Второй раздел

| Команда | Что делает |
| --- | --- |
| `git status` | Показывает состояние трёх «деревьев» |
| `git log --oneline` | Печатает короткую историю |

::: exercise Упражнение
Сформулируйте шаги, которые ученик выполнит самостоятельно, и ожидаемый результат.
:::

## Итоги

Короткое резюме урока и подводка к следующему материалу.

::: quiz Проверка понимания
- ( ) Неверный вариант ответа
- (x) Верный вариант ответа
- ( ) Ещё один неверный вариант

Пояснение: почему верный вариант правильный и что произойдёт при другом выборе.
:::
"""

PAGE_TEMPLATE = """---
title: "{title}"
summary: "Короткое описание страницы."
order: {order}
updated: {today}
icon: "📄"
nav: true
---

Страница материалов курса. Токены сборки: `[[MODULE_MAP]]`, `[[STATS]]`, `[[MODULE_CARDS]]`.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Создать каркас урока или страницы курса")
    parser.add_argument("--module", help="идентификатор модуля (см. --list)")
    parser.add_argument("--title", help="заголовок урока/страницы")
    parser.add_argument("--order", type=int, default=0, help="порядковый номер в модуле")
    parser.add_argument("--slug", help="имя файла без расширения (иначе из заголовка)")
    parser.add_argument("--page", action="store_true", help="создать отдельную страницу в content/pages/")
    parser.add_argument("--list", action="store_true", help="показать модули курса")
    parser.add_argument("--force", action="store_true", help="перезаписать существующий файл")
    args = parser.parse_args(argv)

    config = load_config(ROOT / "site.yml")
    site = load_site(ROOT, config)

    if args.list:
        print("Модули курса:")
        for module in site.modules:
            print(f"  {module.icon} {module.id:<18} {module.title}  ({len(module.lessons)} уроков, content/{module.dir}/)")
        print("\nСтраницы: " + ", ".join(page.slug for page in site.pages))
        return 0

    if not args.title:
        parser.error("нужен --title (или --list)")

    today = date.today().isoformat()
    if args.page:
        slug = args.slug or slugify(args.title)
        target = ROOT / "content" / "pages" / f"{slug}.md"
        order = args.order or (max([p.order for p in site.pages] + [0]) + 1)
        content = PAGE_TEMPLATE.format(title=args.title, order=order, today=today)
    else:
        if not args.module:
            parser.error("нужен --module (список: python3 tools/new_lesson.py --list)")
        module = site.module_by_id(args.module)
        if module is None:
            parser.error(f"модуль {args.module} не найден в content/modules.yml")
        slug = args.slug or slugify(args.title)
        order = args.order or (max([l.order for l in module.lessons] + [0]) + 1)
        target = ROOT / "content" / module.dir / f"{order:02d}-{slug}.md"
        content = LESSON_TEMPLATE.format(title=args.title, order=order, today=today)

    if target.exists() and not args.force:
        print(f"Файл уже существует: {target.relative_to(ROOT)} (перезапись — флагом --force)")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    print(f"Создан файл: {target.relative_to(ROOT)}")
    print(
        "\nЧто дальше:\n"
        "  1. заполните теорию, примеры и вопрос самопроверки;\n"
        "  2. поставьте ссылки через lesson:/page:, а схемы — из assets/img/diagrams/;\n"
        "  3. python3 build.py && python3 tools/validate.py --site site\n"
        "  4. добавьте запись в docs/CHANGELOG.md и запушьте ветку — CI соберёт сайт сам."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
