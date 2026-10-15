"""Мини-парсер YAML-подмножества для конфигов курса (site.yml, modules.yml, front matter).

Поддерживается:

* отображения (вложенность по отступам), списки скаляров, списки отображений;
* инлайн-списки ``[a, b, c]``;
* скаляры: строки в кавычках и без, числа, ``true/false``, ``null``;
* многострочные значения ``>``, ``>-``, ``|``, ``|-``;
* комментарии ``#`` (в конце строки — только для незакавыченных значений).

Не поддерживается (сознательно, чтобы не тащить PyYAML): anchors/aliases, flow-mapping
``{a: b}``, многострочные строки со сложным фолдингом. Если понадобится — добавьте
зависимость в .github/workflows/*.yml и замените вызов на ``yaml.safe_load``.
"""

from __future__ import annotations

import re
from typing import Any


class YamlError(ValueError):
    """Ошибка разбора мини-YAML."""


def _split_comment(value: str) -> str:
    out: list[str] = []
    quote: str | None = None
    for ch in value:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).strip()


def _scalar(raw: str) -> Any:
    raw = _split_comment(raw)
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    low = raw.lower()
    if low in {"true", "yes", "on"}:
        return True
    if low in {"false", "no", "off"}:
        return False
    if low in {"null", "none", "~", ""}:
        return None if raw == "" or low != "" else None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [] if not inner else [_scalar(part) for part in inner.split(",")]
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw


def _prepare(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.strip() == "---":
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip() if raw.strip().startswith("-") else raw.rstrip()[indent:]))
    return lines


def _parse_block(lines: list[tuple[int, str]], idx: int, indent: int) -> tuple[Any, int]:
    if idx >= len(lines):
        return None, idx
    if lines[idx][1].startswith("-"):
        return _parse_list(lines, idx, indent)
    return _parse_map(lines, idx, indent)


def _parse_map(lines: list[tuple[int, str]], idx: int, indent: int) -> tuple[dict, int]:
    result: dict[str, Any] = {}
    while idx < len(lines):
        cur_indent, content = lines[idx]
        if cur_indent < indent or content.startswith("-"):
            break
        if cur_indent > indent:
            raise YamlError(f"Неожиданный отступ: {content!r}")
        if ":" not in content:
            raise YamlError(f"Ожидалось 'ключ: значение', получено {content!r}")
        key, _, value = content.partition(":")
        key = key.strip()
        value = value.strip()
        idx += 1
        if value in {">", ">-", "|", "|-"}:
            collected: list[str] = []
            while idx < len(lines) and lines[idx][0] > indent:
                collected.append(lines[idx][1])
                idx += 1
            joiner = " " if value.startswith(">") else "\n"
            result[key] = joiner.join(collected)
        elif value == "":
            if idx < len(lines) and lines[idx][0] > indent:
                result[key], idx = _parse_block(lines, idx, lines[idx][0])
            elif idx < len(lines) and lines[idx][0] == indent and lines[idx][1].startswith("-"):
                result[key], idx = _parse_list(lines, idx, indent)
            else:
                result[key] = None
        else:
            result[key] = _scalar(value)
    return result, idx


def _parse_list(lines: list[tuple[int, str]], idx: int, indent: int) -> tuple[list, int]:
    items: list[Any] = []
    while idx < len(lines):
        cur_indent, content = lines[idx]
        if cur_indent != indent or not content.startswith("-"):
            break
        item_text = content[1:].lstrip()
        idx += 1
        if not item_text:
            nested, idx = _parse_block(lines, idx, lines[idx][0]) if idx < len(lines) else (None, idx)
            items.append(nested)
            continue
        if ":" in item_text and not item_text.startswith(("\"", "'")):
            sub_indent = indent + 2
            sub_lines = [(sub_indent, item_text)]
            while idx < len(lines) and lines[idx][0] > indent:
                line_indent, line_content = lines[idx]
                sub_lines.append((max(sub_indent + (line_indent - indent - 2), sub_indent), line_content))
                idx += 1
            value, _ = _parse_map(sub_lines, 0, sub_indent)
            items.append(value)
            continue
        items.append(_scalar(item_text))
    return items, idx


def loads(text: str) -> Any:
    lines = _prepare(text)
    if not lines:
        return {}
    value, _ = _parse_block(lines, 0, lines[0][0])
    return value
