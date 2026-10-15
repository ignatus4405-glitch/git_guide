"""Конвертер Markdown → HTML для сайта курса.

Поддерживается подмножество GitHub Flavored Markdown плюс расширения,
которые нужны курсу (см. docs/CONTENT_GUIDE.md):

* заголовки ``#``…``######`` с якорями и авто-TOC;
* абзацы, списки (в т.ч. вложенные и задачи ``- [x]``), цитаты, таблицы, ``---``;
* блоки кода с языком, подписью и подсветкой: ```` ```bash title="git log" ````;
* врезки-выноски ``::: warning Заголовок`` … ``:::`` (note/tip/info/warning/danger/
  success/details/exercise/goal);
* тест ``::: quiz Вопрос`` со вариантами ``- (x) верный`` / ``- ( ) неверный``;
* картинки с подписью: ``![alt](assets/img/x.svg "Подпись")`` → ``<figure>``;
* разрешённый «сырой» HTML (``<kbd>``, ``<details>``, ``<sup>``…), скрипты запрещены;
* внутренние ссылки-схемы: ``lesson:slug``, ``page:slug``, ``module:id``.

Рендерер ничего не знает про структуру сайта: разрешение ссылок делает
переданная снаружи функция ``resolve`` (см. tools/content.py и build.py).
"""

from __future__ import annotations

import html
import re
from typing import Callable

from .highlight import highlight, normalize_lang

Resolver = Callable[[str, str], str]

_CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}

# Теги, которые разрешено писать прямо в Markdown.
_ALLOWED_TAGS = {
    "a", "abbr", "aside", "b", "br", "code", "col", "colgroup", "dd", "del", "details",
    "div", "dl", "dt", "em", "figcaption", "figure", "h3", "h4", "h5", "i", "img",
    "ins", "kbd", "li", "mark", "ol", "p", "pre", "s", "samp", "section", "small",
    "span", "strong", "sub", "summary", "sup", "table", "tbody", "td", "tfoot", "th",
    "thead", "tr", "u", "ul", "var", "wbr",
}
_CONTAINER_TAGS = {"div", "details", "section", "aside", "figure", "table", "ul", "ol", "dl", "p"}

_TAG_RE = re.compile(r"</?([A-Za-z][A-Za-z0-9-]*)(?:\s[^<>]*)?/?>")
_ON_ATTR_RE = re.compile(r"\s+on[a-z]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
_JS_URL_RE = re.compile(r"(?i)javascript:[^\"'\s>]*")
_DANGEROUS_BLOCK_RE = re.compile(r"<(script|style|iframe|object|embed|form)\b[\s\S]*?</\1\s*>", re.I)


def sanitize_html(text: str) -> str:
    """Убирает из «сырого» HTML опасные конструкции, оставляя разметку курса.

    Контент курса пишут люди и агенты, поэтому HTML в разметке проходит санитайзинг:
    обработчики событий (``onclick`` и подобные), ссылки ``javascript:`` и блоки
    ``<script>/<style>/<iframe>`` удаляются. Остальная разметка сохраняется как есть.
    """
    text = _DANGEROUS_BLOCK_RE.sub("", text)
    text = _ON_ATTR_RE.sub("", text)
    text = _JS_URL_RE.sub("#", text)
    return text

_ADMONITIONS = {
    "note": ("📝", "Заметка", "adm--note"),
    "info": ("ℹ️", "Справка", "adm--info"),
    "tip": ("💡", "Полезный приём", "adm--tip"),
    "success": ("✅", "Готово", "adm--success"),
    "warning": ("⚠️", "Важно", "adm--warning"),
    "danger": ("⛔", "Опасно", "adm--danger"),
    "exercise": ("🏋️", "Упражнение", "adm--exercise"),
    "goal": ("🎯", "Цель урока", "adm--goal"),
    "details": ("🔎", "Подробнее", "adm--details"),
    "terminal": ("🖥️", "Терминал", "adm--terminal"),
    "quiz": ("🧩", "Проверь себя", "adm--quiz"),
    "history": ("📜", "Историческая справка", "adm--history"),
}

_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([^`~]*)$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_UL_RE = re.compile(r"^(\s*)([-*+])\s+(.*)$")
_OL_RE = re.compile(r"^(\s*)(\d{1,3})[.)]\s+(.*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_INFO_RE = re.compile(r"^(?P<lang>[A-Za-z0-9+#._-]*)\s*(?P<rest>.*)$")


def slugify(text: str) -> str:
    """Латинизирует заголовок в стабильный якорь (кириллица → латиница)."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.lower()
    out = []
    for ch in text:
        if ch in _CYRILLIC:
            out.append(_CYRILLIC[ch])
        elif ch.isalnum() and ch.isascii():
            out.append(ch)
        elif ch in " \t-–—_/.":
            out.append("-")
    slug = re.sub(r"-{2,}", "-", "".join(out)).strip("-")
    return slug or "section"


def _is_raw_html(line: str) -> str | None:
    m = re.match(r"^\s*<(/?)([A-Za-z][A-Za-z0-9-]*)\b", line)
    if not m:
        return None
    tag = m.group(2).lower()
    return tag if tag in _ALLOWED_TAGS else None


class MarkdownRenderer:
    def __init__(self, resolve: Resolver | None = None, *, features: set[str] | None = None):
        self.resolve = resolve or (lambda kind, value: value)
        self.toc: list[dict] = []
        self._slug_counts: dict[str, int] = {}
        self.features = features if features is not None else {"tables", "quizzes"}

    # ------------------------------------------------------------------ API
    def render(self, text: str) -> str:
        self.toc = []
        self._slug_counts = {}
        blocks = self._parse_blocks(text.replace("\r\n", "\n").split("\n"))
        return "\n".join(blocks)

    # ------------------------------------------------------------- блочный слой
    def _parse_blocks(self, lines: list[str]) -> list[str]:
        out: list[str] = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]

            if not line.strip():
                i += 1
                continue

            fence = _FENCE_RE.match(line)
            if fence:
                i = self._render_fence(lines, i, out)
                continue

            if line.lstrip().startswith(":::"):
                i = self._render_admonition(lines, i, out)
                continue

            heading = _HEADING_RE.match(line)
            if heading:
                out.append(self._render_heading(heading.group(1), heading.group(2)))
                i += 1
                continue

            if _HR_RE.match(line):
                out.append("<hr>")
                i += 1
                continue

            if line.lstrip().startswith(">"):
                i = self._render_quote(lines, i, out)
                continue

            if self._list_match(line):
                i = self._render_list(lines, i, out)
                continue

            if self._is_table_start(lines, i):
                i = self._render_table(lines, i, out)
                continue

            raw_tag = _is_raw_html(line)
            if raw_tag or line.lstrip().startswith("<!--"):
                i = self._render_raw_html(lines, i, out, raw_tag)
                continue

            i = self._render_paragraph(lines, i, out)
        return out

    @staticmethod
    def _list_match(line: str):
        return _UL_RE.match(line) or _OL_RE.match(line)

    def _render_heading(self, hashes: str, title: str) -> str:
        level = len(hashes)
        plain = re.sub(r"[`*_]", "", title).strip()
        slug = slugify(plain)
        count = self._slug_counts.get(slug, 0)
        self._slug_counts[slug] = count + 1
        anchor = slug if count == 0 else f"{slug}-{count}"
        if 2 <= level <= 4:
            self.toc.append({"level": level, "id": anchor, "text": plain})
        inner = self._inline(title)
        return (
            f'<h{level} id="{anchor}"><a class="anchor" href="#{anchor}" '
            f'aria-hidden="true">#</a>{inner}</h{level}>'
        )

    def _render_fence(self, lines: list[str], i: int, out: list[str]) -> int:
        indent, marker, info = _FENCE_RE.match(lines[i]).groups()
        i += 1
        body: list[str] = []
        while i < len(lines) and not re.match(r"^\s*" + re.escape(marker[0]) + r"{3,}\s*$", lines[i]):
            body.append(lines[i])
            i += 1
        i += 1  # закрывающий забор (или конец файла)

        info = info.strip()
        m = _INFO_RE.match(info)
        lang = normalize_lang(m.group("lang") if m else "")
        rest = m.group("rest") if m else ""
        title_m = re.search(r'title="([^"]*)"', rest)
        caption = title_m.group(1) if title_m else ""
        numbered = "linenos" in rest or "number" in rest

        code = "\n".join(body)
        if indent:
            code = "\n".join(l[len(indent) :] if l.startswith(indent) else l for l in code.split("\n"))

        numbered_html = ""
        if numbered and code:
            width = len(str(code.count("\n") + 1))
            rows = "".join(
                f'<span class="ln">{idx:>{width}}</span>' for idx in range(1, code.count("\n") + 2)
            )
            numbered_html = f'<span class="linenos" aria-hidden="true">{rows}\n</span>'

        lang_label = lang if lang and lang != "text" else "text"
        out.append(
            '<div class="code" data-lang="{lang}">'
            '<div class="code__bar"><span class="code__lang">{lang}</span>{title}'
            '<button class="code__copy" type="button" data-copy>Скопировать</button></div>'
            '<pre><code class="language-{lang}">{numbers}{code}</code></pre></div>'.format(
                lang=html.escape(lang_label),
                title=f'<span class="code__title">{html.escape(caption)}</span>' if caption else "",
                numbers=numbered_html,
                code=highlight(code, lang),
            )
        )
        return i

    def _render_admonition(self, lines: list[str], i: int, out: list[str]) -> int:
        header = lines[i].lstrip()[3:].strip()
        i += 1
        body: list[str] = []
        depth = 1
        while i < len(lines):
            stripped = lines[i].lstrip()
            if stripped.startswith(":::"):
                depth -= 1
                if depth <= 0:
                    i += 1
                    break
            body.append(lines[i])
            i += 1

        kind, _, title = header.partition(" ")
        kind = kind.strip().lower() or "note"
        title = title.strip().strip('"')

        if kind == "quiz":
            out.append(self._render_quiz(title, body))
            return i

        if kind == "columns":
            parts = self._split_columns(body)
            out.append(
                '<div class="columns">'
                + "".join(f'<div class="column">{self.render(p)}</div>' for p in parts)
                + "</div>"
            )
            return i

        emoji, default_title, css = _ADMONITIONS.get(kind, _ADMONITIONS["note"])
        title_html = html.escape(title) if title else default_title
        inner = self.render("\n".join(body))

        if kind == "details":
            out.append(
                f'<details class="adm {css}"><summary><span class="adm__icon">{emoji}</span>'
                f'<span class="adm__title">{title_html}</span></summary>'
                f'<div class="adm__body">{inner}</div></details>'
            )
        else:
            out.append(
                f'<div class="adm {css}"><p class="adm__head"><span class="adm__icon">{emoji}</span>'
                f'<span class="adm__title">{title_html}</span></p>'
                f'<div class="adm__body">{inner}</div></div>'
            )
        return i

    @staticmethod
    def _split_columns(body: list[str]) -> list[str]:
        parts: list[list[str]] = [[]]
        for line in body:
            if line.strip() in {"---", "|||"}:
                parts.append([])
                continue
            parts[-1].append(line)
        return ["\n".join(p).strip() for p in parts]

    def _render_quiz(self, question: str, body: list[str]) -> str:
        options: list[tuple[bool, str]] = []
        explanation: list[str] = []
        for line in body:
            m = re.match(r"^\s*[-*]\s+\(([xX +\-)]?)\)\s*(.*)$", line)
            if m:
                mark, text = m.groups()
                options.append((mark.lower() == "x", text.strip()))
            elif line.strip():
                explanation.append(line.strip())
        item_id = f"quiz-{len(self.toc)}-{abs(hash(question)) % 100000}"
        html_opts = []
        for idx, (correct, text) in enumerate(options):
            html_opts.append(
                f'<button class="quiz__opt" type="button" data-correct="{1 if correct else 0}" '
                f'data-i="{idx}"><span class="quiz__mark">{chr(65 + idx)}</span>'
                f'<span class="quiz__text">{self._inline(text)}</span></button>'
            )
        explain = (
            f'<div class="quiz__explain">{self._inline(" ".join(explanation))}</div>'
            if explanation
            else ""
        )
        return (
            f'<div class="quiz" id="{item_id}" data-quiz>'
            f'<p class="adm__head"><span class="adm__icon">🧩</span>'
            f'<span class="adm__title">{html.escape(question) or "Проверь себя"}</span></p>'
            + "".join(html_opts)
            + explain
            + '<p class="quiz__done" hidden>Отличная работа! Вариант выделен верно.</p>'
            "</div>"
        )

    def _render_quote(self, lines: list[str], i: int, out: list[str]) -> int:
        body: list[str] = []
        while i < len(lines) and (lines[i].lstrip().startswith(">") or not lines[i].strip()):
            if not lines[i].strip():
                body.append("")
                i += 1
                continue
            body.append(re.sub(r"^\s*>\s?", "", lines[i]))
            i += 1
        out.append(f"<blockquote>{self.render(chr(10).join(body).strip())}</blockquote>")
        return i

    def _render_list(self, lines: list[str], i: int, out: list[str]) -> int:
        start_match = _OL_RE.match(lines[i])
        ordered = bool(start_match)
        base_indent = len(lines[i]) - len(lines[i].lstrip())
        items: list[list[str]] = []
        current: list[str] = []
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                # пустая строка внутри списка: продолжаем, если далее отступ достаточный
                lookahead = i + 1
                if lookahead < len(lines):
                    nxt = lines[lookahead]
                    indent = len(nxt) - len(nxt.lstrip())
                    if nxt.strip() and indent >= base_indent:
                        current.append("")
                        i += 1
                        continue
                break
            indent = len(line) - len(line.lstrip())
            marker = _UL_RE.match(line) or _OL_RE.match(line)
            if marker and indent <= base_indent + 1:
                if current:
                    items.append(current)
                current = [marker.group(3)]
                i += 1
                continue
            if indent > base_indent or (marker and indent <= base_indent + 1):
                strip = min(indent, base_indent + 2)
                current.append(line[strip:] if len(line) > strip else line.strip())
                i += 1
                continue
            break
        if current:
            items.append(current)

        rendered = []
        task_list = False
        for item in items:
            first = item[0] if item else ""
            task = re.match(r"^\[([ xX])\]\s*(.*)$", first)
            checkbox = ""
            if task:
                task_list = True
                checked = task.group(1).lower() == "x"
                checkbox = (
                    f'<input type="checkbox" disabled{" checked" if checked else ""}> '
                )
                item[0] = task.group(2)
            inner = self.render("\n".join(item).strip())
            inner = re.sub(r"^<p>(.*)</p>$", r"\1", inner, flags=re.S)
            rendered.append(f"<li>{checkbox}{inner}</li>")

        tag = "ol" if ordered else "ul"
        attrs = ""
        if ordered and start_match and start_match.group(2) != "1":
            attrs = f' start="{int(start_match.group(2))}"'
        if task_list:
            attrs += ' class="task-list"'
        out.append(f"<{tag}{attrs}>" + "".join(rendered) + f"</{tag}>")
        return i

    def _is_table_start(self, lines: list[str], i: int) -> bool:
        if "tables" not in self.features:
            return False
        if i + 1 >= len(lines):
            return False
        head = lines[i]
        sep = lines[i + 1]
        if "|" not in head.strip("|"):
            return False
        return bool(_TABLE_SEP_RE.match(sep)) and "-" in sep

    def _render_table(self, lines: list[str], i: int, out: list[str]) -> int:
        def cells(row: str) -> list[str]:
            row = row.strip()
            if row.startswith("|"):
                row = row[1:]
            if row.endswith("|"):
                row = row[:-1]
            return [c.strip() for c in re.split(r"(?<!\\)\|", row)]

        header = cells(lines[i])
        aligns = []
        for col in cells(lines[i + 1]):
            left = col.startswith(":")
            right = col.endswith(":")
            aligns.append("center" if left and right else "right" if right else "left")
        i += 2
        rows: list[list[str]] = []
        while i < len(lines) and lines[i].strip() and "|" in lines[i]:
            rows.append(cells(lines[i]))
            i += 1

        thead = "".join(
            f'<th style="text-align:{aligns[idx] if idx < len(aligns) else "left"}">'
            f"{self._inline(c)}</th>"
            for idx, c in enumerate(header)
        )
        tbody = ""
        for row in rows:
            tds = "".join(
                f'<td style="text-align:{aligns[idx] if idx < len(aligns) else "left"}">'
                f"{self._inline(c)}</td>"
                for idx, c in enumerate(row)
            )
            tbody += f"<tr>{tds}</tr>"
        out.append(
            f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead>'
            f"<tbody>{tbody}</tbody></table></div>"
        )
        return i

    def _render_raw_html(self, lines: list[str], i: int, out: list[str], tag: str | None) -> int:
        collected: list[str] = []
        closing = None
        if tag and tag in _CONTAINER_TAGS:
            closing = re.compile(rf"</{tag}\s*>", re.IGNORECASE)
        while i < len(lines):
            line = lines[i]
            if not line.strip() and collected and closing is None:
                break
            if not line.strip() and collected and closing is not None and closing.search("\n".join(collected)):
                break
            collected.append(line)
            if closing is not None and closing.search(line):
                i += 1
                break
            if closing is None and (not line.strip()):
                break
            i += 1
        out.append(sanitize_html("\n".join(collected)))
        return i

    def _render_paragraph(self, lines: list[str], i: int, out: list[str]) -> int:
        buf: list[str] = []
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            if buf and (
                _FENCE_RE.match(line)
                or _HEADING_RE.match(line)
                or _HR_RE.match(line)
                or self._list_match(line)
                or line.lstrip().startswith((">", ":::"))
                or self._is_table_start(lines, i)
                or _is_raw_html(line)
            ):
                break
            buf.append(line.strip())
            i += 1
        out.append(f"<p>{self._inline(' '.join(buf))}</p>")
        return i

    # ------------------------------------------------------------ инлайн-слой
    def _inline(self, text: str) -> str:
        placeholders: dict[str, str] = {}

        def stash(payload: str) -> str:
            key = f"\x00{len(placeholders)}\x00"
            placeholders[key] = payload
            return key

        # 1. Разрешённый inline-HTML сохраняем как есть (экранирование не применяем).
        def keep_tag(m: re.Match[str]) -> str:
            tag = m.group(0)
            name = m.group(1).lower()
            if name not in _ALLOWED_TAGS:
                return html.escape(tag)
            return stash(sanitize_html(tag))

        text = _TAG_RE.sub(keep_tag, text)

        # 2. Экранируем остальное.
        text = html.escape(text, quote=False)

        # 3. Код в бэктиках.
        def code_span(m: re.Match[str]) -> str:
            return stash(f"<code>{html.escape(m.group(2))}</code>")

        text = re.sub(r"(`+)(.+?)\1", code_span, text, flags=re.S)

        # 4. Картинки ![alt](src "title")
        def image(m: re.Match[str]) -> str:
            alt, src, title = m.group(1), m.group(2), m.group(3)
            src = self.resolve("asset", src)
            caption = title or alt
            return stash(
                f'<figure><img src="{html.escape(src, quote=True)}" '
                f'alt="{html.escape(re.sub(chr(60) + "[^>]+" + chr(62), "", alt), quote=True)}" loading="lazy">'
                + (f"<figcaption>{self._inline(caption)}</figcaption>" if caption else "")
                + "</figure>"
            )

        text = re.sub(r"!\[([^\]]*)\]\(([^\s)]+)(?:\s+\"([^\"]*)\")?\)", image, text)

        # 5. Ссылки [текст](цель "title")
        def link(m: re.Match[str]) -> str:
            label, target, title = m.group(1), m.group(2), m.group(3)
            href = self._resolve_link(target)
            title_attr = f' title="{html.escape(title)}"' if title else ""
            return stash(f'<a href="{html.escape(href, quote=True)}"{title_attr}>{label}</a>')

        text = re.sub(r"\[([^\]]+)\]\(([^\s)]+)(?:\s+\"([^\"]*)\")?\)", link, text)

        # 6. Автоссылки на голые URL.
        text = re.sub(
            r"(?<![\"'=])(https?://[^\s<>\u0000)\]]+)",
            lambda m: stash(
                f'<a href="{html.escape(m.group(1), quote=True)}" target="_blank" '
                f'rel="noopener">{html.escape(m.group(1))}</a>'
            ),
            text,
        )

        # 7. Выделения.
        text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text, flags=re.S)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.S)
        text = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", text)
        text = re.sub(r"(?<![\w_])_([^_\n]+?)_(?![\w_])", r"<em>\1</em>", text)
        text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text, flags=re.S)
        text = re.sub(r"==(.+?)==", r"<mark>\1</mark>", text, flags=re.S)

        # 8. Возвращаем сохранённые куски.
        for key, payload in placeholders.items():
            text = text.replace(key, payload)
        return text

    def _resolve_link(self, target: str) -> str:
        if target.startswith(("lesson:", "page:", "module:")):
            kind, _, value = target.partition(":")
            return self.resolve(kind, value)
        if target.startswith(("http://", "https://", "mailto:", "#", "/")):
            return target
        return self.resolve("asset", target)
