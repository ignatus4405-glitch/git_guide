"""Подсветка синтаксиса без внешних зависимостей.

Это «честный» маленький подсветчик: для каждого языка задан упорядоченный список
правил (комментарий, строка, число, ключевое слово, встроенная команда, опция,
переменная). Сканер идёт по исходнику слева направо, на каждой позиции пробует
правила по порядку и на первом совпадении заворачивает текст в ``<span class="tok-*">``.
Если ничего не совпало — символ попадает в вывод как обычный текст.

Гарантии:
* весь исходный текст попадает в вывод ровно один раз (никаких «потерянных» хвостов);
* всё, что выводится, экранируется, поэтому подсветка не может сломать HTML страницы.
"""

from __future__ import annotations

import html
import re

# --- классы токенов (см. assets/css/site.css) -------------------------------
# tok-com  комментарий          tok-str  строка
# tok-num  число                tok-key  ключевое слово
# tok-cmd  имя команды          tok-opt  опция/флаг
# tok-var  переменная           tok-op   оператор/пунктуация
# tok-prompt приглашение '$ '   tok-add/tok-del diff-строки

_RULES: dict[str, list[tuple[str, re.Pattern[str]]]] = {}


def _add(lang: str, *rules: tuple[str, str]) -> None:
    compiled = [(cls, re.compile(pat)) for cls, pat in rules]
    _RULES[lang] = compiled


_COMMENT_HASH = ("tok-com", r"#[^\n]*")
_INSERT_DELETE = (
    ("tok-add", r"^\+[^\n]*"),
    ("tok-del", r"^-[^\n]*"),
    ("tok-com", r"^@@[^\n]*"),
)

_add(
    "bash",
    ("tok-prompt", r"^\$ |^> "),
    _COMMENT_HASH,
    ("tok-str", r"'[^'\n]*'|\"[^\"\n]*\""),
    ("tok-var", r"\$\{?[A-Za-z_][\w]*\}?|\$[0-9@*#?!]"),
    (
        "tok-cmd",
        r"\b(?:git|gh|npm|npx|node|python3?|pip|make|curl|wget|ssh|scp|openssl|tar|zip|unzip|"
        r"cat|echo|cd|ls|mkdir|rm|cp|mv|touch|chmod|grep|sed|awk|find|export|source|sudo|apt|"
        r"brew|docker|kubectl|jq|base64|git-lfs|hub|code|vim|nano|less|head|tail|wc|diff|patch|"
        r"gitkraken|act)\b",
    ),
    (
        "tok-key",
        r"\b(?:if|then|else|elif|fi|for|do|done|while|case|esac|function|return|local|read|"
        r"set|unset|exit|trap|in)\b",
    ),
    ("tok-opt", r"(?<=\s)--?[A-Za-z][\w-]*"),
    ("tok-num", r"\b\d+(?:\.\d+)?\b"),
    ("tok-op", r"[|&;()<>{}]"),
)
_add("shell", *_RULES["bash"])
_add("console", *_RULES["bash"])
_add("sh", *_RULES["bash"])
_add("git", *_RULES["bash"])

_add(
    "yaml",
    _COMMENT_HASH,
    ("tok-str", r"'[^'\n]*'|\"[^\"\n]*\""),
    ("tok-key", r"^[ \t-]*[A-Za-z_][\w.-]*(?=\s*:)"),
    ("tok-var", r"\$\{\{[^}]+\}\}|\$\{\{|\}\}"),
    ("tok-num", r"\b\d+(?:\.\d+)?\b"),
    ("tok-op", r"[:|>-]"),
)
_add("yml", *_RULES["yaml"])

_add(
    "json",
    ("tok-key", r"\"[\w@./-]+\"(?=\s*:)"),
    ("tok-str", r"\"(?:[^\"\\\n]|\\.)*\""),
    ("tok-num", r"\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
    ("tok-key", r"\b(?:true|false|null)\b"),
    ("tok-op", r"[{}\[\],:]"),
)

_add(
    "python",
    _COMMENT_HASH,
    ("tok-str", r"\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|f?\"(?:[^\"\\\n]|\\.)*\"|f?'(?:[^'\\\n]|\\.)*'"),
    (
        "tok-key",
        r"\b(?:def|class|return|if|elif|else|for|while|in|import|from|as|with|try|except|"
        r"finally|raise|pass|break|continue|lambda|yield|global|nonlocal|assert|del|async|await|"
        r"and|or|not|is|None|True|False|self)\b",
    ),
    ("tok-cmd", r"\b(?:print|len|range|str|int|float|list|dict|set|tuple|open|enumerate|zip|"
                  r"sum|min|max|sorted|isinstance|super|type)\b"),
    ("tok-num", r"\b\d+(?:\.\d+)?\b"),
    ("tok-op", r"[+\-*/%=<>!&|^~]+"),
)

_add(
    "javascript",
    _COMMENT_HASH,
    ("tok-com", r"//[^\n]*"),
    ("tok-str", r"`(?:[^`\\]|\\.)*`|\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*'"),
    (
        "tok-key",
        r"\b(?:const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|"
        r"new|class|extends|super|this|import|export|from|default|async|await|try|catch|finally|"
        r"throw|typeof|instanceof|null|undefined|true|false|of|in|delete|void|yield)\b",
    ),
    ("tok-cmd", r"\b(?:console|document|window|JSON|Object|Array|String|Number|Boolean|Promise|"
                  r"fetch|Math|Date|process|require|module|localStorage)\b"),
    ("tok-num", r"\b\d+(?:\.\d+)?\b"),
    ("tok-op", r"[+\-*/%=<>!&|^~?:]+"),
)
_add("js", *_RULES["javascript"])
_add("typescript", *_RULES["javascript"])
_add("ts", *_RULES["javascript"])

_add(
    "dockerfile",
    _COMMENT_HASH,
    (
        "tok-key",
        r"(?i)^\s*(?:FROM|RUN|CMD|LABEL|MAINTAINER|EXPOSE|ENV|ADD|COPY|ENTRYPOINT|VOLUME|"
        r"USER|WORKDIR|ARG|ONBUILD|STOPSIGNAL|HEALTHCHECK|SHELL|AS)\b",
    ),
    ("tok-str", r"'[^'\n]*'|\"[^\"\n]*\""),
    ("tok-var", r"\$\{?[A-Za-z_][\w]*\}?"),
    ("tok-num", r"\b\d+\b"),
)
_add("docker", *_RULES["dockerfile"])

_add(
    "ini",
    _COMMENT_HASH,
    ("tok-com", r";[^\n]*"),
    ("tok-key", r"^\s*\[[^\]\n]+\]"),
    ("tok-key", r"^[A-Za-z_][\w.-]*(?=\s*=)"),
    ("tok-num", r"\b\d+(?:\.\d+)?\b"),
)
_add("toml", *_RULES["ini"])
_add("properties", *_RULES["ini"])

_add(
    "html",
    ("tok-com", r"<!--[\s\S]*?-->"),
    ("tok-key", r"</?[A-Za-z][\w-]*"),
    ("tok-str", r"\"[^\"\n]*\"|'[^'\n]*'"),
    ("tok-op", r"[<>/=]"),
)
_add("xml", *_RULES["html"])
_add("svg", *_RULES["html"])

_add("diff", *_INSERT_DELETE, ("tok-key", r"^diff --git[^\n]*"), ("tok-opt", r"^[+-]{3}[^\n]*"))

_add(
    "sql",
    ("tok-com", r"--[^\n]*"),
    ("tok-str", r"'[^'\n]*'"),
    (
        "tok-key",
        r"(?i)\b(?:SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|INDEX|"
        r"ALTER|DROP|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP|ORDER|BY|HAVING|LIMIT|OFFSET|AS|AND|"
        r"OR|NOT|NULL|PRIMARY|KEY|FOREIGN|REFERENCES|DEFAULT|UNIQUE|CHECK|CASCADE)\b",
    ),
    ("tok-num", r"\b\d+\b"),
)

_add(
    "markdown",
    ("tok-key", r"^#{1,6} [^\n]*"),
    ("tok-com", r"<!--[\s\S]*?-->"),
    ("tok-str", r"`[^`\n]*`|\*\*[^*\n]+\*\*"),
    ("tok-op", r"^\s*[-*+]\s|^\s*\d+\.\s|^>"),
)
_add("md", *_RULES["markdown"])

_add(
    "powershell",
    _COMMENT_HASH,
    ("tok-str", r"'[^'\n]*'|\"[^\"\n]*\""),
    ("tok-var", r"\$[A-Za-z_][\w]*"),
    (
        "tok-key",
        r"(?i)\b(?:if|else|elseif|foreach|while|function|param|return|try|catch|finally|throw|"
        r"switch|break|continue|New-Item|Remove-Item|Get-ChildItem|Set-Location|Write-Host)\b",
    ),
    ("tok-opt", r"(?<=\s)-[A-Za-z][\w-]*"),
)
_add("ps1", *_RULES["powershell"])
_add("pwsh", *_RULES["powershell"])

_add("text",)
_add("plaintext",)
_add("plain",)

_ALIASES = {
    "": "text",
    "text": "text",
    "txt": "text",
    "bash": "bash",
    "zsh": "bash",
    "shell": "bash",
    "console": "bash",
    "sh": "bash",
    "gitconfig": "ini",
    "editorconfig": "ini",
    "env": "bash",
    "dotenv": "bash",
    "github-actions": "yaml",
    "workflow": "yaml",
    "actions": "yaml",
}


def normalize_lang(lang: str) -> str:
    lang = (lang or "").strip().lower()
    if lang in _ALIASES:
        return _ALIASES[lang]
    return lang if lang in _RULES else "text"


def supported_languages() -> list[str]:
    return sorted(k for k in _RULES if k not in _ALIASES)


def highlight(code: str, lang: str = "") -> str:
    """Возвращает HTML-фрагмент с подсвеченным кодом (без обёртки <pre><code>)."""
    code = code.replace("\r\n", "\n").rstrip("\n")
    rules = _RULES.get(normalize_lang(lang)) or []
    if not rules:
        return html.escape(code)

    out: list[str] = []
    i = 0
    size = len(code)
    plain_start = i

    def flush(end: int) -> None:
        nonlocal plain_start
        if end > plain_start:
            out.append(html.escape(code[plain_start:end]))

    while i < size:
        matched = False
        for cls, pattern in rules:
            m = pattern.match(code, i)
            if m and m.end() > i:
                flush(i)
                out.append(f'<span class="{cls}">{html.escape(m.group(0))}</span>')
                i = m.end()
                plain_start = i
                matched = True
                break
        if not matched:
            i += 1
    flush(size)
    return "".join(out)
