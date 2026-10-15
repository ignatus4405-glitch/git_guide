#!/usr/bin/env python3
"""Локальный предпросмотр собранного сайта.

Запуск::

    python3 tools/serve.py                 # http://0.0.0.0:8000
    python3 tools/serve.py --port 5000 --build

Сервер отдаёт каталог сборки (по умолчанию ``site/``), включает правильные MIME-типы
для ``.json``/``.svg``, отдаёт ``404.html`` на неизвестные адреса и отключает листинг
каталогов. Зависимостей нет — только стандартная библиотека.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import mimetypes
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build import ROOT, main as build_main  # noqa: E402

mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("text/plain; charset=utf-8", ".txt")


class Handler(http.server.SimpleHTTPRequestHandler):
    """Отдаёт файлы сборки; неизвестные пути → 404.html."""

    server_version = "GitGuidePreview/1.0"

    def send_head(self):
        path = self.translate_path(self.path)
        target = Path(path)
        if target.is_dir():
            index = target / "index.html"
            if index.exists():
                self.path = str(index.relative_to(self.directory))
            else:
                return self.send_error(404, "Каталог без index.html", self.error_page())
        elif not target.exists():
            return self.send_error(404, "Страница не найдена", self.error_page())
        return super().send_head()

    def error_page(self) -> str:
        page = Path(self.directory) / "404.html"
        return page.read_text(encoding="utf-8") if page.exists() else "404"

    def send_error(self, code, message=None, explain=None):
        if code == 404 and explain:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            return self.wfile.write(explain.encode("utf-8"))
        return super().send_error(code, message, explain)

    def log_message(self, fmt, *args):  # тише лог: только код и путь
        sys.stderr.write("  %s\n" % (fmt % args))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Предпросмотр собранного сайта курса")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument("--host", default="0.0.0.0", help="адрес прослушивания")
    parser.add_argument("--dir", default="site", help="каталог сборки")
    parser.add_argument("--build", action="store_true", help="пересобрать сайт перед запуском")
    args = parser.parse_args(argv)

    if args.build or not (ROOT / args.dir).exists():
        print("Сборка сайта…")
        build_main(["--out", args.dir, "--quiet"])

    handler = functools.partial(Handler, directory=str(ROOT / args.dir))
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        print(f"Сайт курса доступен: http://{args.host}:{args.port}/ (Ctrl+C — остановить)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nОстановлено.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
