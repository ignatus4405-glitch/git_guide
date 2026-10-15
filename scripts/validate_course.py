#!/usr/bin/env python3
"""Validate the Russian course data before the Windows application is built."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
COURSE_PATH = REPOSITORY_ROOT / "Course" / "lessons.json"
ALLOWED_BLOCK_TYPES = {"heading", "text", "paragraph", "bullet", "code", "note"}


def load_course(path: Path = COURSE_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as course_file:
        return json.load(course_file)


def validate_course(course: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not isinstance(course, dict):
        return ["Корневое значение курса должно быть JSON-объектом."]

    for required in ("courseTitle", "courseSubtitle", "lessons"):
        if not course.get(required):
            errors.append(f"Не заполнено обязательное поле курса: {required}.")

    lessons = course.get("lessons")
    if not isinstance(lessons, list) or len(lessons) < 18:
        errors.append("Курс должен содержать список как минимум из 18 уроков.")
        return errors

    seen_ids: set[str] = set()
    for number, lesson in enumerate(lessons, start=1):
        prefix = f"Урок {number}"
        if not isinstance(lesson, dict):
            errors.append(f"{prefix}: должен быть JSON-объектом.")
            continue

        for required in ("id", "section", "title", "lead", "practice"):
            if not isinstance(lesson.get(required), str) or not lesson[required].strip():
                errors.append(f"{prefix}: отсутствует непустое строковое поле {required}.")

        lesson_id = lesson.get("id")
        if isinstance(lesson_id, str):
            if lesson_id in seen_ids:
                errors.append(f"{prefix}: повторяется id {lesson_id!r}.")
            seen_ids.add(lesson_id)

        duration = lesson.get("durationMinutes")
        if not isinstance(duration, int) or not 1 <= duration <= 90:
            errors.append(f"{prefix}: durationMinutes должно быть целым числом от 1 до 90.")

        blocks = lesson.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            errors.append(f"{prefix}: требуется хотя бы один блок с объяснением.")
        else:
            for block_number, block in enumerate(blocks, start=1):
                if not isinstance(block, dict):
                    errors.append(f"{prefix}, блок {block_number}: должен быть объектом.")
                    continue
                block_type = block.get("type")
                if block_type not in ALLOWED_BLOCK_TYPES:
                    errors.append(f"{prefix}, блок {block_number}: неизвестный тип {block_type!r}.")
                if not isinstance(block.get("text"), str) or not block["text"].strip():
                    errors.append(f"{prefix}, блок {block_number}: text должен быть непустой строкой.")

        diagram = lesson.get("diagram")
        if not isinstance(diagram, dict) or not diagram.get("title") or not diagram.get("caption"):
            errors.append(f"{prefix}: нужна схема с названием и пояснением.")
        elif not isinstance(diagram.get("steps"), list) or len(diagram["steps"]) < 3:
            errors.append(f"{prefix}: схема должна содержать не менее трёх шагов.")
        else:
            for step_number, step in enumerate(diagram["steps"], start=1):
                if not isinstance(step, dict) or not step.get("title") or not step.get("detail"):
                    errors.append(f"{prefix}, шаг схемы {step_number}: нужны title и detail.")

        quiz = lesson.get("quiz")
        if not isinstance(quiz, dict) or not quiz.get("question") or not quiz.get("explanation"):
            errors.append(f"{prefix}: нужна контрольная задача с объяснением.")
        else:
            options = quiz.get("options")
            answer = quiz.get("answerIndex")
            if not isinstance(options, list) or len(options) < 2 or any(not str(item).strip() for item in options):
                errors.append(f"{prefix}: в тесте должно быть не менее двух непустых вариантов.")
            elif not isinstance(answer, int) or not 0 <= answer < len(options):
                errors.append(f"{prefix}: answerIndex выходит за границы списка вариантов.")

    return errors


def main() -> int:
    try:
        course = load_course()
    except (OSError, json.JSONDecodeError) as error:
        print(f"Не удалось прочитать {COURSE_PATH}: {error}", file=sys.stderr)
        return 1

    errors = validate_course(course)
    if errors:
        print("Проверка курса завершилась с ошибками:", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1

    print(f"Курс проверен: {len(course['lessons'])} уроков, схемы и тесты заполнены.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
