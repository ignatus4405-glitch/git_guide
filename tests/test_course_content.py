import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from validate_course import load_course, validate_course  # noqa: E402


class CourseContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.course = load_course()

    def test_course_data_is_valid(self):
        self.assertEqual(validate_course(self.course), [])

    def test_course_has_a_visual_and_quiz_for_every_lesson(self):
        for lesson in self.course["lessons"]:
            with self.subTest(lesson=lesson["id"]):
                self.assertGreaterEqual(len(lesson["diagram"]["steps"]), 3)
                self.assertGreaterEqual(len(lesson["quiz"]["options"]), 2)
                self.assertTrue(lesson["practice"].strip())

    def test_course_covers_core_git_and_github_workflows(self):
        all_lesson_text = "\n".join(
            block.get("text", "")
            for lesson in self.course["lessons"]
            for block in lesson["blocks"]
        )
        for expected in (
            "git status",
            "git add",
            "git commit",
            "git push",
            "git pull",
            "git revert",
            "Pull Request",
            "GitHub Actions",
            "gh pr create",
        ):
            with self.subTest(term=expected):
                self.assertIn(expected, all_lesson_text)

    def test_validator_rejects_duplicate_ids_and_bad_quiz_index(self):
        broken = {
            "courseTitle": "Test",
            "courseSubtitle": "Test",
            "lessons": [
                {
                    "id": "same",
                    "section": "Test",
                    "title": "Test",
                    "level": "Начинающий",
                    "durationMinutes": 5,
                    "lead": "Тест",
                    "blocks": [{"type": "text", "text": "Тест"}],
                    "diagram": {
                        "title": "Схема",
                        "caption": "Тест",
                        "steps": [
                            {"title": "A", "detail": "A"},
                            {"title": "B", "detail": "B"},
                            {"title": "C", "detail": "C"},
                        ],
                    },
                    "practice": "Тест",
                    "quiz": {
                        "question": "Тест?",
                        "options": ["A", "B"],
                        "answerIndex": 5,
                        "explanation": "Тест",
                    },
                },
                {
                    "id": "same",
                    "section": "Test",
                    "title": "Test 2",
                    "level": "Начинающий",
                    "durationMinutes": 5,
                    "lead": "Тест",
                    "blocks": [{"type": "text", "text": "Тест"}],
                    "diagram": {
                        "title": "Схема",
                        "caption": "Тест",
                        "steps": [
                            {"title": "A", "detail": "A"},
                            {"title": "B", "detail": "B"},
                            {"title": "C", "detail": "C"},
                        ],
                    },
                    "practice": "Тест",
                    "quiz": {
                        "question": "Тест?",
                        "options": ["A", "B"],
                        "answerIndex": 0,
                        "explanation": "Тест",
                    },
                },
            ],
        }
        broken["lessons"] *= 9
        errors = validate_course(broken)
        self.assertTrue(any("повторяется id" in error for error in errors))
        self.assertTrue(any("answerIndex" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
