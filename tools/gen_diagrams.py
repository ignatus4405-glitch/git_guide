"""Генератор SVG-схем курса («диаграммы как код»).

Почему так: картинки-схемы в курсе должны быть воспроизводимыми, версионируемыми
и правимыми одним PR-ом. Поэтому они не нарисованы в редакторе, а описаны кодом —
векторные файлы попадают в собранный сайт (``site/assets/img/diagrams/``) при
каждой сборке и не хранятся в репозитории (см. .gitignore → /site/).

Запуск отдельно::

    python3 tools/gen_diagrams.py --out site/assets/img/diagrams

Каждая функция возвращает строку SVG. Имена файлов перечислены в :data:`DIAGRAMS`,
этот словарь использует валидатор контента, чтобы ловить ссылки на несуществующие схемы.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

FONT = "Inter, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def wrap(text: str, width: int) -> list[str]:
    """Переносит подпись по словам так, чтобы строка не длиннее width символов."""
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class Canvas:
    """Крошечный SVG-билдер: прямоугольники, стрелки, подписи, легенда."""

    def __init__(self, width: int, height: int, title: str, desc: str):
        self.width = width
        self.height = height
        self.title = title
        self.desc = desc
        self.body: list[str] = []

    # ------------------------------------------------------------ примитивы
    def box(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        subtitle: str = "",
        *,
        fill: str = "#ffffff",
        stroke: str = "#d0d7de",
        text: str = "#1f2328",
        radius: float = 12,
        dash: str = "",
        title_size: int = 16,
        mono: bool = False,
        badge: str = "",
        wrap_at: int = 22,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.body.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" ry="{radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"{dash_attr}/>'
        )
        font = MONO if mono else FONT
        lines = wrap(title, wrap_at)
        subtitle_lines = wrap(subtitle, int(wrap_at * 1.5)) if subtitle else []
        total = len(lines) * (title_size + 4) + (len(subtitle_lines) * 15 if subtitle_lines else 0)
        cursor = y + h / 2 - total / 2 + title_size
        for line in lines:
            self.body.append(
                f'<text x="{x + w / 2}" y="{cursor}" font-family="{font}" font-size="{title_size}" '
                f'font-weight="600" fill="{text}" text-anchor="middle">{_esc(line)}</text>'
            )
            cursor += title_size + 4
        for line in subtitle_lines:
            self.body.append(
                f'<text x="{x + w / 2}" y="{cursor}" font-family="{FONT}" font-size="12.5" '
                f'fill="#57606a" text-anchor="middle">{_esc(line)}</text>'
            )
            cursor += 15
        if badge:
            self.body.append(
                f'<rect x="{x + 10}" y="{y - 11}" width="{8 + len(badge) * 7.2}" height="20" rx="10" '
                f'fill="{stroke}" opacity="0.16"/>'
                f'<text x="{x + 14}" y="{y + 3}" font-family="{FONT}" font-size="11.5" '
                f'font-weight="700" fill="{stroke}">{_esc(badge)}</text>'
            )

    def arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str = "",
        *,
        color: str = "#57606a",
        dashed: bool = False,
        width: float = 2,
        curve: float | None = None,
        label_dx: float = 0,
        label_dy: float = -8,
        label_size: int = 12.5,
        mono: bool = True,
        marker: str = "arrow",
    ) -> None:
        dash_attr = ' stroke-dasharray="6 5"' if dashed else ""
        if curve is None:
            path = f"M {x1} {y1} L {x2} {y2}"
        else:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2 + curve
            path = f"M {x1} {y1} Q {cx} {cy} {x2} {y2}"
        self.body.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'marker-end="url(#{marker})"{dash_attr} stroke-linecap="round"/>'
        )
        if label:
            mx, my = (x1 + x2) / 2 + label_dx, (y1 + y2) / 2 + label_dy
            if curve is not None:
                my += curve * 0.75
            font = MONO if mono else FONT
            self.body.append(
                f'<text x="{mx}" y="{my}" font-family="{font}" font-size="{label_size}" '
                f'fill="{color}" text-anchor="middle" '
                f'paint-order="stroke" stroke="#ffffff" stroke-width="4" '
                f'stroke-linejoin="round">{_esc(label)}</text>'
            )

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        size: float = 13,
        color: str = "#1f2328",
        anchor: str = "start",
        weight: str = "400",
        mono: bool = False,
    ) -> None:
        font = MONO if mono else FONT
        self.body.append(
            f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}">{_esc(value)}</text>'
        )

    def pill(
        self,
        x: float,
        y: float,
        label: str,
        *,
        fill: str = "#eef2f6",
        color: str = "#1f2328",
        mono: bool = True,
        size: float = 12.5,
    ) -> float:
        w = 18 + len(label) * (size * 0.62)
        self.body.append(
            f'<rect x="{x}" y="{y}" width="{w:.0f}" height="24" rx="12" fill="{fill}"/>'
            f'<text x="{x + w / 2:.0f}" y="{y + 16.5}" font-family="{MONO if mono else FONT}" '
            f'font-size="{size}" fill="{color}" text-anchor="middle">{_esc(label)}</text>'
        )
        return w

    def circle_commit(
        self,
        cx: float,
        cy: float,
        label: str,
        *,
        fill: str = "#2f81f7",
        r: float = 17,
        text_color: str = "#ffffff",
    ) -> None:
        self.body.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="#ffffff" stroke-width="2"/>'
            f'<text x="{cx}" y="{cy + 5}" font-family="{MONO}" font-size="12.5" font-weight="700" '
            f'fill="{text_color}" text-anchor="middle">{_esc(label)}</text>'
        )

    def legend(self, x: float, y: float, items: list[tuple[str, str]]) -> None:
        cursor = x
        for color, label in items:
            self.body.append(f'<circle cx="{cursor + 22}" cy="{y - 4}" r="6" fill="{color}"/>')
            self.body.append(
                f'<text x="{cursor + 34}" y="{y}" font-family="{FONT}" font-size="12" '
                f'fill="#57606a">{_esc(label)}</text>'
            )
            cursor += 34 + len(label) * 6.6 + 26

    # -------------------------------------------------------------- сборка
    def render(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" '
            f'width="100%" role="img" aria-labelledby="t d" preserveAspectRatio="xMidYMid meet">'
            f'<title id="t">{_esc(self.title)}</title><desc id="d">{_esc(self.desc)}</desc>'
            "<defs>"
            '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#57606a"/></marker>'
            '<marker id="arrowOrange" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#f05033"/></marker>'
            '<marker id="arrowBlue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#2f81f7"/></marker>'
            '<marker id="arrowGreen" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#3fb950"/></marker>'
            '<marker id="arrowPurple" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#a371f7"/></marker>'
            '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0%" stop-color="#f6f8fa"/><stop offset="100%" stop-color="#ffffff"/>'
            "</linearGradient>"
            "</defs>"
            f'<rect width="{self.width}" height="{self.height}" fill="url(#sky)"/>'
            + "".join(self.body)
            + "</svg>"
        )


C_ORANGE, C_BLUE, C_GREEN, C_PURPLE = "#f05033", "#2f81f7", "#3fb950", "#a371f7"
C_INK, C_MUTED, C_LINE = "#1f2328", "#57606a", "#d0d7de"


# --------------------------------------------------------------------- схемы
def three_trees() -> str:
    c = Canvas(940, 430, "Три дерева Git", "Рабочий каталог, область подготовки и репозиторий")
    c.text(30, 42, "Три «дерева» Git: где живут ваши изменения", size=20, weight="700")
    c.text(30, 66, "Пока файл не прошёл весь путь слева направо, GitHub о нём ничего не знает.", size=13, color=C_MUTED)

    boxes = [
        (30, "Рабочий каталог", "working tree — файлы на диске", C_BLUE),
        (350, "Область подготовки", "staging area / index — будущий коммит", C_ORANGE),
        (670, "Репозиторий", ".git — история коммитов", C_GREEN),
    ]
    for x, title, sub, color in boxes:
        c.box(x, 130, 240, 120, title, sub, fill="#ffffff", stroke=color, wrap_at=20)

    c.arrow(272, 172, 348, 172, "git add", color=C_ORANGE, marker="arrowOrange")
    c.arrow(272, 212, 348, 212, "git add -p", color=C_ORANGE, dashed=True, marker="arrowOrange", label_dy=24)
    c.arrow(592, 172, 668, 172, "git commit", color=C_GREEN, marker="arrowGreen")
    c.arrow(592, 212, 668, 212, "git commit --amend", color=C_GREEN, dashed=True, marker="arrowGreen", label_dy=24)
    c.arrow(350, 262, 272, 262, "git restore --staged", color=C_MUTED, dashed=True)
    c.arrow(668, 262, 592, 262, "git reset --soft", color=C_MUTED, dashed=True)

    c.box(670, 300, 240, 96, "GitHub (remote)", "origin — общая копия репозитория", fill="#ffffff", stroke=C_PURPLE, wrap_at=20)
    c.arrow(790, 252, 790, 298, "git push", color=C_PURPLE, marker="arrowPurple")
    c.arrow(750, 298, 750, 254, "git fetch", color=C_MUTED, dashed=True, label_dx=-4)

    c.text(30, 340, "git status показывает расхождение между", size=13, color=C_INK)
    c.text(30, 360, "всеми тремя слоями сразу.", size=13, color=C_INK, weight="600")
    c.box(30, 300, 240, 96, "Рабочий каталог ← → HEAD", "git status · git diff · git diff --staged", fill="#f6f8fa", stroke=C_LINE, wrap_at=20, title_size=14)
    return c.render()


def commit_internals() -> str:
    c = Canvas(940, 470, "Устройство коммита", "Коммит ссылается на дерево и родителя, дерево — на блобы")
    c.text(30, 42, "Из чего состоит коммит", size=20, weight="700")
    c.text(30, 66, "SHA-1 считается от содержимого: изменился один символ — изменился весь объект.", size=13, color=C_MUTED)

    c.box(30, 120, 250, 130, "commit 9f2a1c4", "tree, parent, author, message", fill="#fff4f0", stroke=C_ORANGE, mono=True, wrap_at=18, title_size=15)
    c.box(360, 120, 230, 130, "tree 4c1d8e0", "снимок каталога проекта", fill="#f0f7ff", stroke=C_BLUE, wrap_at=18)
    c.box(670, 120, 240, 130, "parent 7b3e002", "предыдущий коммит (может быть 2+ у merge)", fill="#f0fff4", stroke=C_GREEN, wrap_at=18, title_size=14)

    c.arrow(280, 185, 358, 185, "указывает на", color=C_BLUE, marker="arrowBlue", mono=False)
    c.arrow(590, 185, 668, 185, "указывает на", color=C_GREEN, marker="arrowGreen", mono=False)

    blobs = [
        (30, "blob 8ac2f19\nREADME.md"),
        (300, "blob 1de4b77\nbuild.py"),
        (570, "blob 77c9a02\ntools/md.py"),
        (840, ""),
    ]
    for idx, (x, label) in enumerate(blobs[:3]):
        name, sub = label.split("\n")
        c.box(x, 320, 220, 100, name, sub, fill="#ffffff", stroke=C_LINE, mono=True, wrap_at=16, title_size=14)
        c.arrow(475, 250, x + 110, 318, "", color=C_LINE, dashed=True)

    c.text(360, 305, "дерево описывает имена, режимы и хеши содержимого", size=12.5, color=C_MUTED)
    c.legend(30, 452, [(C_ORANGE, "объект коммита"), (C_BLUE, "дерево"), (C_GREEN, "родитель"), (C_LINE, "блобы файлов")])
    return c.render()


def branches_merge() -> str:
    c = Canvas(940, 420, "Ветка и слияние", "Ветка — подвижный указатель на коммит")
    c.text(30, 42, "Ветка — это всего лишь подвижная метка", size=20, weight="700")
    c.text(30, 66, "HEAD показывает, где вы находитесь; git switch меняет указатель, а не файлы вручную.", size=13, color=C_MUTED)

    y_main, y_feat = 170, 280
    for idx, (x, sha) in enumerate([(120, "A1"), (250, "B2"), (380, "C3"), (700, "M5")]):
        c.circle_commit(x, y_main, sha, fill=C_BLUE)
    c.circle_commit(510, y_feat, "D4", fill=C_ORANGE)

    c.arrow(137, y_main, 233, y_main, color=C_LINE)
    c.arrow(267, y_main, 363, y_main, color=C_LINE)
    c.arrow(397, y_main, 683, y_main, color=C_LINE)
    c.arrow(380, y_main + 20, 505, y_feat - 18, "git switch -c feature", color=C_ORANGE, curve=20, label_dy=6, marker="arrowOrange")
    c.arrow(527, y_feat - 16, 690, y_main + 18, "git merge feature", color=C_GREEN, curve=-20, label_dy=-10)

    c.pill(60, y_main - 46, "main", fill="#e7f0fd", color=C_BLUE)
    c.pill(480, y_feat + 26, "feature/login", fill="#fdeee8", color=C_ORANGE)
    c.pill(640, y_main - 46, "main → M5", fill="#e8f8ec", color=C_GREEN)

    c.box(30, 330, 420, 70, "Fast-forward", "main просто догоняет feature: отдельного merge-коммита нет", fill="#f6f8fa", stroke=C_LINE, wrap_at=34, title_size=14)
    c.box(470, 330, 440, 70, "Merge-коммит", "появляется, когда main уже ушёл вперёд: у коммита два родителя", fill="#f6f8fa", stroke=C_LINE, wrap_at=40, title_size=14)
    return c.render()


def merge_vs_rebase() -> str:
    c = Canvas(940, 470, "merge против rebase", "Две стратегии встраивания ветки")
    c.text(30, 42, "Merge и Rebase: разница в истории", size=20, weight="700")
    c.text(30, 66, "Обе команды дают одинаковый код. Разной будет история — и цена повторного применения коммитов.", size=13, color=C_MUTED)

    # Левая панель — merge
    c.box(30, 100, 430, 330, "", "", fill="#ffffff", stroke=C_BLUE, wrap_at=10)
    c.text(52, 132, "git merge feature", size=16, weight="700", color=C_BLUE, mono=True)
    c.text(52, 156, "История ветвится, видно, где была ветка.", size=12.5, color=C_MUTED)
    for x, sha in [(110, "A"), (200, "B"), (290, "M")]:
        c.circle_commit(x, 215, sha, fill=C_BLUE)
    c.arrow(127, 215, 183, 215, color=C_LINE)
    c.arrow(217, 215, 273, 215, color=C_LINE)
    c.circle_commit(200, 300, "C", fill=C_ORANGE)
    c.arrow(215, 285, 282, 232, color=C_GREEN, curve=-6)
    c.pill(52, 330, "merge-коммит M", fill="#e8f8ec", color=C_GREEN)
    c.text(52, 396, ".git остаётся честной хроникой работы.", size=12.5, color=C_MUTED, mono=False)

    # Правая панель — rebase
    c.box(480, 100, 430, 330, "", "", fill="#ffffff", stroke=C_ORANGE, wrap_at=10)
    c.text(502, 132, "git rebase main", size=16, weight="700", color=C_ORANGE, mono=True)
    c.text(502, 156, "История линейная, коммиты переприменены (новые SHA).", size=12.5, color=C_MUTED)
    for x, sha in [(560, "A"), (650, "B"), (740, "C*"), (830, "D*")]:
        c.circle_commit(x, 215, sha, fill=C_ORANGE if sha.endswith("*") else C_BLUE)
    c.arrow(577, 215, 633, 215, color=C_LINE)
    c.arrow(667, 215, 723, 215, color=C_LINE)
    c.arrow(757, 215, 813, 215, color=C_LINE)
    c.pill(502, 260, "коммиты переписаны", fill="#fdeee8", color=C_ORANGE)
    c.text(502, 330, "Правило: не перебазируйте общие ветки —", size=12.5, color=C_INK, mono=False)
    c.text(502, 350, "у коллег останутся старые SHA.", size=12.5, color=C_INK, mono=False, weight="600")
    c.text(502, 396, "Зато диффом приятно читать.", size=12.5, color=C_MUTED, mono=False)
    return c.render()


def conflict_resolution() -> str:
    c = Canvas(940, 430, "Разрешение конфликта слияния", "Как Git показывает конфликт и что делать дальше")
    c.text(30, 42, "Конфликт слияния: что происходит внутри файла", size=20, weight="700")
    c.text(30, 66, "Git не выбирает сам, если обе ветки изменили одну и ту же строку.", size=13, color=C_MUTED)

    c.box(30, 110, 430, 170, "Ветка main", "currency.py → rate = 1.10", fill="#f0f7ff", stroke=C_BLUE, mono=True, wrap_at=26, title_size=14)
    c.box(480, 110, 430, 170, "Ветка feature", "currency.py → rate = 1.12  + кэш", fill="#fff4f0", stroke=C_ORANGE, mono=True, wrap_at=26, title_size=14)
    c.arrow(460, 195, 478, 195, "конфликт", color=C_ORANGE, marker="arrowOrange", mono=False, label_dy=-12)

    c.box(30, 300, 880, 100, "После git merge: маркеры <<<<<<< ======= >>>>>>>", "правите файл вручную → git add currency.py → git commit", fill="#f6f8fa", stroke=C_GREEN, wrap_at=60, title_size=14, mono=False)
    return c.render()


def reset_vs_revert() -> str:
    c = Canvas(940, 430, "reset, revert, restore", "Отмена изменений на трёх уровнях")
    c.text(30, 42, "Как отменить изменения и не потерять работу", size=20, weight="700")
    rows = [
        ("git restore file", "Выбрасывает правки в рабочем каталоге", "Обратимо, только локально", C_BLUE),
        ("git reset --soft HEAD^", "Убирает последний коммит, правки остаются в индексе", "Меняет локальную историю", C_ORANGE),
        ("git revert <sha>", "Создаёт новый коммит, отменяющий указанный", "Безопасно для общих ветвей", C_GREEN),
    ]
    y = 110
    for cmd, what, when, color in rows:
        c.box(30, y, 880, 86, "", "", fill="#ffffff", stroke=color, wrap_at=10, radius=12)
        c.text(52, y + 36, cmd, size=15, weight="700", color=color, mono=True)
        c.text(52, y + 62, what, size=12.5, color=C_INK)
        c.text(700, y + 62, when, size=12, color=C_MUTED, anchor="start")
        y += 100
    c.legend(30, 415, [(C_BLUE, "рабочий каталог"), (C_ORANGE, "локальная история"), (C_GREEN, "публичная история")])
    return c.render()


def remote_and_pr() -> str:
    c = Canvas(940, 470, "Удалённые репозитории и Pull Request", "Полный путь изменения от вашей машины до main")
    c.text(30, 42, "Путь одного изменения: от ветки до слияния в main", size=20, weight="700")
    c.text(30, 66, "origin — ваш форк или общий репозиторий, upstream — исходный проект.", size=13, color=C_MUTED)

    c.box(30, 120, 200, 100, "Локальный репозиторий", "git switch -c fix/docs", fill="#f0f7ff", stroke=C_BLUE, wrap_at=18, title_size=14)
    c.box(290, 120, 180, 100, "origin", "ваш форк на GitHub", fill="#fff4f0", stroke=C_ORANGE, wrap_at=16)
    c.box(530, 120, 180, 100, "upstream", "репозиторий проекта", fill="#f6f8fa", stroke=C_MUTED, wrap_at=16)
    c.box(760, 120, 150, 100, "Pull Request", "обсуждение и ревью", fill="#f0fff4", stroke=C_GREEN, wrap_at=14, title_size=14)

    c.arrow(232, 152, 288, 152, "git push -u origin", color=C_ORANGE, marker="arrowOrange", label_dy=-10)
    c.arrow(472, 170, 528, 170, "git fetch upstream", color=C_MUTED, dashed=True, label_dy=20)
    c.arrow(712, 170, 758, 170, "gh pr create", color=C_GREEN, marker="arrowGreen", label_dy=-10)
    c.arrow(835, 220, 835, 275, "review", color=C_GREEN, marker="arrowGreen", label_dy=6)

    c.box(560, 275, 350, 90, "Merge в main → origin", "squash · rebase · merge-commit", fill="#ffffff", stroke=C_GREEN, wrap_at=30, title_size=14)
    c.arrow(560, 320, 460, 320, "git pull --rebase", color=C_MUTED, dashed=True, label_dy=-12)
    c.box(30, 275, 400, 90, "Ваш локальный main снова актуален", "git fetch && git rebase origin/main", fill="#f6f8fa", stroke=C_BLUE, wrap_at=34, title_size=14)

    c.pill(30, 396, "origin/feature = ветка-«отправка»", fill="#fdeee8", color=C_ORANGE)
    c.pill(300, 396, "исходный проект не трогаем напрямую", fill="#e7f0fd", color=C_BLUE)
    c.text(30, 448, "Правило хорошего PR: одна задача, маленький дифф, понятное описание, зелёные проверки.", size=13, color=C_INK, weight="600")
    return c.render()


def actions_pipeline() -> str:
    c = Canvas(940, 470, "Пайплайн GitHub Actions", "Событие запускает набор задач, артефакт попадает на Pages")
    c.text(30, 42, "Как этот курс собирается в GitHub Actions", size=20, weight="700")
    c.text(30, 66, "Workflow → jobs → steps. Джобы идут параллельно, если нет needs.", size=13, color=C_MUTED)

    c.box(30, 120, 170, 96, "Событие", "push · pull_request · workflow_dispatch · schedule", fill="#f6f8fa", stroke=C_MUTED, wrap_at=16, title_size=15)
    jobs = [
        (240, "validate", "проверка контента и ссылок", C_BLUE),
        (410, "test", "самотесты сборки", C_PURPLE),
        (580, "build", "генерация site/ + схемы", C_ORANGE),
        (750, "deploy", "artifact → GitHub Pages", C_GREEN),
    ]
    for x, title, sub, color in jobs:
        c.box(x, 120, 160, 96, title, sub, fill="#ffffff", stroke=color, wrap_at=15, title_size=15)
    for idx in range(len(jobs) - 1):
        left, right = jobs[idx], jobs[idx + 1]
        c.arrow(left[0] + 160, 168, right[0], 168, "needs", color=C_LINE, dashed=True, label_dy=-10)

    c.box(30, 280, 880, 90, "Шаги задачи build", "checkout → setup-python → python3 build.py → загрузка артефакта site/", fill="#ffffff", stroke=C_ORANGE, wrap_at=70, title_size=14)
    c.text(30, 400, "Итог: каждая ссылка в курсе проверяется автоматически, а сайт обновляется без ручных действий.", size=13, color=C_INK)
    c.pill(30, 415, "permissions: contents: read — минимум прав", fill="#e7f0fd", color=C_BLUE)
    c.pill(430, 415, "concurrency: отмена устаревших запусков", fill="#e8f8ec", color=C_GREEN)
    return c.render()


def workflows_compare() -> str:
    c = Canvas(940, 470, "Стратегии ветвления", "GitHub Flow, Git Flow и Trunk-based")
    c.text(30, 42, "Какую модель ветвления выбрать", size=20, weight="700")
    panels = [
        (30, "GitHub Flow", "main + короткие ветки, всё через Pull Request", ["main всегда готова к деплою", "ветка живёт 1–3 дня", "CI обязателен"], C_GREEN),
        (340, "Git Flow", "develop, release, hotfix — много долгих ветвей", ["релизы по расписанию", "сложнее слияния", "для упакованного ПО"], C_BLUE),
        (650, "Trunk-based", "все коммитят в main, ветки на часы", ["feature flags", "высокая частота релизов", "нужны строгие проверки"], C_PURPLE),
    ]
    for x, title, sub, bullets, color in panels:
        c.box(x, 110, 270, 300, title, sub, fill="#ffffff", stroke=color, wrap_at=22, title_size=17)
        y = 240
        for b in bullets:
            c.text(x + 26, y, "• " + b, size=12.5, color=C_INK)
            y += 26
    c.text(30, 440, "Для опенсорса и небольших команд почти всегда выигрывает GitHub Flow.", size=13, color=C_INK, weight="600")
    return c.render()


def security_layers() -> str:
    c = Canvas(940, 440, "Слои безопасности репозитория", "От паролей до сканирования зависимостей")
    c.text(30, 42, "Защита проекта: пять слоёв", size=20, weight="700")
    layers = [
        (30, "Аутентификация", "SSH-ключ или PAT + 2FA", C_BLUE),
        (215, "Права", "роли, CODEOWNERS, ветки-правила", C_ORANGE),
        (400, "Секреты", "Secrets, OIDC, push protection", C_PURPLE),
        (585, "Код", "Dependabot, CodeQL, secret scanning", C_GREEN),
        (770, "Процесс", "ревью, подписанные коммиты, аудит", C_INK),
    ]
    for x, title, sub, color in layers:
        c.box(x, 110, 155, 130, title, sub, fill="#ffffff", stroke=color, wrap_at=13, title_size=15)
    c.arrow(60, 260, 900, 260, "чем правее — тем раньше ловим проблему, но тем дороже настройка в начале", color=C_MUTED, mono=False, label_dy=-12, label_size=12)
    c.text(30, 300, "Минимум для любого публичного репозитория:", size=14, weight="700")
    for idx, item in enumerate([
        "включить 2FA: без него GitHub блокирует push в публичные репозитории",
        "не коммитить .env — использовать GitHub Secrets",
        "добавить branch protection на main: обязательный PR и зелёный CI",
        "включить Dependabot alerts и secret scanning",
    ]):
        c.text(30, 330 + idx * 26, "→ " + item, size=12.5, color=C_INK)
    return c.render()


def lesson_anatomy() -> str:
    c = Canvas(940, 430, "Анатомия урока курса", "Из каких частей состоит учебный материал")
    c.text(30, 42, "Как устроен каждый урок", size=20, weight="700")
    blocks = [
        (30, "Front matter", "title, summary, order, goals, updated", C_BLUE),
        (250, "Цели", "что вы будете уметь после урока", C_ORANGE),
        (470, "Теория + схемы", "объяснения, SVG-диаграммы, таблицы", C_GREEN),
        (690, "Практика", "команды с разбором вывода и ошибок", C_PURPLE),
        (30 + 220 * 4, "", "", C_INK),
    ]
    for x, title, sub, color in blocks[:4]:
        c.box(x, 110, 200, 110, title, sub, fill="#ffffff", stroke=color, wrap_at=17, title_size=15)
    c.box(30, 260, 880, 70, "Проверка себя", "quiz-вопросы в конце урока + итоговый экзамен курса", fill="#f6f8fa", stroke=C_LINE, wrap_at=60, title_size=14)
    c.text(30, 360, "Каждый блок урока доступен как markdown в content/: курс правится как обычный код.", size=13, color=C_MUTED)
    return c.render()


def fork_sync() -> str:
    c = Canvas(940, 400, "Синхронизация форка", "Как поддерживать форк в актуальном состоянии")
    c.text(30, 42, "Форк и его синхронизация с upstream", size=20, weight="700")
    c.box(30, 110, 260, 100, "upstream/main", "исходный проект", fill="#f6f8fa", stroke=C_MUTED, wrap_at=18)
    c.box(350, 110, 260, 100, "origin/main", "ваш форк на GitHub", fill="#fff4f0", stroke=C_ORANGE, wrap_at=18)
    c.box(670, 110, 240, 100, "local main", "ваш компьютер", fill="#f0f7ff", stroke=C_BLUE, wrap_at=18)
    c.arrow(292, 150, 348, 150, "Sync fork", color=C_GREEN, marker="arrowGreen", mono=False, label_dy=-10)
    c.arrow(612, 150, 668, 150, "git pull", color=C_BLUE, marker="arrowBlue", label_dy=-10)
    c.arrow(670, 190, 612, 190, "git push", color=C_ORANGE, marker="arrowOrange", dashed=True, label_dy=20)
    c.text(30, 260, "Вариант без веб-интерфейса — явные remote-и:", size=14, weight="700")
    c.text(30, 292, "git remote add upstream git@github.com:OWNER/REPO.git", size=13, mono=True)
    c.text(30, 318, "git fetch upstream && git switch main && git rebase upstream/main", size=13, mono=True)
    c.text(30, 344, "git push origin main --force-with-lease   # только для своей ветки!", size=13, mono=True, color=C_ORANGE)
    c.text(30, 380, "force-with-lease безопаснее --force: push будет отклонён, если на сервере появились чужие коммиты.", size=12.5, color=C_MUTED)
    return c.render()


def submodule_or_lfs() -> str:
    c = Canvas(940, 400, "Большие файлы и подмодули", "Что делать с тяжёлыми данными в репозитории")
    c.text(30, 42, "Большие файлы: LFS и подмодули", size=20, weight="700")
    c.box(30, 110, 430, 120, "Git LFS", "указатель в Git, содержимое — во внешнем хранилище", fill="#ffffff", stroke=C_ORANGE, wrap_at=32, title_size=16)
    c.text(56, 190, "git lfs track \"*.psd\"  →  .gitattributes", size=12.5, mono=True, color=C_MUTED)
    c.box(480, 110, 430, 120, "git submodule", "чужой репозиторий внутри своего на фиксированном коммите", fill="#ffffff", stroke=C_BLUE, wrap_at=36, title_size=16)
    c.text(506, 190, "git submodule add <url> vendor/lib", size=12.5, mono=True, color=C_MUTED)
    c.text(30, 260, "Когда НЕ нужно:", size=14, weight="700")
    for idx, item in enumerate([
        "файл < 50 МБ и меняется редко — Git справится сам",
        "данные генерируются на CI — не коммитьте их вовсе",
        "нужна только часть истории — git clone --depth 1",
    ]):
        c.text(30, 290 + idx * 26, "→ " + item, size=12.5, color=C_INK)
    c.pill(620, 250, "GitHub отклоняет файлы > 100 МБ", fill="#fdeee8", color=C_ORANGE)
    return c.render()


DIAGRAMS: dict[str, callable] = {
    "three-trees.svg": three_trees,
    "commit-internals.svg": commit_internals,
    "branches-merge.svg": branches_merge,
    "merge-vs-rebase.svg": merge_vs_rebase,
    "conflict-resolution.svg": conflict_resolution,
    "reset-vs-revert.svg": reset_vs_revert,
    "remote-and-pr.svg": remote_and_pr,
    "actions-pipeline.svg": actions_pipeline,
    "workflows-compare.svg": workflows_compare,
    "security-layers.svg": security_layers,
    "lesson-anatomy.svg": lesson_anatomy,
    "fork-sync.svg": fork_sync,
    "large-files.svg": submodule_or_lfs,
}


def write_all(target: Path) -> list[str]:
    """Пишет все схемы в каталог target и возвращает список имён файлов."""
    target.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, builder in DIAGRAMS.items():
        (target / name).write_text(builder(), encoding="utf-8")
        written.append(name)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Генератор SVG-схем курса")
    parser.add_argument("--out", default="site/assets/img/diagrams", help="каталог вывода")
    args = parser.parse_args()
    written = write_all(Path(args.out))
    print(f"Схем сгенерировано: {len(written)} → {args.out}")
    for name in written:
        print(f"  · {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
