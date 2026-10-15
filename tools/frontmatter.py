"""Разбор front matter markdown-файлов курса.

Front matter — это YAML-подобный блок в начале файла::

    ---
    title: "Заголовки и чтение истории"
    order: 4
    updated: 2026-10-15
    tags: [git, log]
    goals:
      - Читать однострочный лог
    ---

Разбор делегируется :mod:`tools.yamlmini`, поэтому поддерживаются вложенность,
списки, кавычки, числа, булевы значения и многострочные скаляры. Внешние
зависимости не нужны: сборка курса должна работать на голом Python.
"""

from __future__ import annotations

from typing import Any

from . import yamlmini


class FrontMatterError(ValueError):
    """Ошибка разбора front matter."""


def parse(text: str) -> tuple[dict[str, Any], str]:
    """Возвращает (метаданные, тело документа без front matter)."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() in {"---", "..."}:
            end = idx
            break
    if end is None:
        raise FrontMatterError("Открыт front matter (---), но закрывающий --- не найден")
    header = "\n".join(lines[1:end])
    try:
        meta = yamlmini.loads(header) or {}
    except yamlmini.YamlError as exc:  # pragma: no cover - защита от кривого контента
        raise FrontMatterError(f"Не удалось разобрать front matter: {exc}") from exc
    if not isinstance(meta, dict):
        raise FrontMatterError("Front matter должен быть отображением ключ: значение")
    body = "\n".join(lines[end + 1 :])
    return meta, body.lstrip("\n")
