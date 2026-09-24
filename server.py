#!/usr/bin/env python3
"""MLB 포스트시즌 대진표 서버.

정적 파일과 서버 렌더링 페이지(대진표, 팀별 상대전적, 리그별 순위, 소개)를 제공한다.
MLB Stats API 호출(순위 1번 + 관련 팀 일정 최대 12번)은 30분에 한 번만 하고, 그 결과를 재사용한다.
"""
import datetime
import json
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import bracket
import pages
import pages_en

CACHE_SECONDS = 1800       # 순위는 하루 몇 번만 바뀌므로 30분 재사용으로 충분하다
STALE_MAX_SECONDS = 3600 * 6  # 조회가 실패하면 최대 6시간 전 데이터를 대신 보여준다
RETRY_AFTER_SECONDS = 120  # 조회가 실패하면 2분 동안은 다시 호출하지 않는다

_cache = {"at": 0.0, "payload": None, "retry_at": 0.0, "error": None}
_cache_lock = threading.Lock()


def get_payload():
    with _cache_lock:
        now = time.time()
        payload = _cache["payload"]
        if payload and now - _cache["at"] < CACHE_SECONDS:
            return payload
        if now < _cache["retry_at"]:
            if payload and now - _cache["at"] < STALE_MAX_SECONDS:
                return payload
            raise RuntimeError(_cache["error"])
        try:
            fresh = bracket.build_bracket()
        except Exception as e:  # noqa: BLE001
            _cache["retry_at"] = now + RETRY_AFTER_SECONDS
            _cache["error"] = str(e)
            if payload and now - _cache["at"] < STALE_MAX_SECONDS:
                return payload
            raise
        _cache.update(at=now, payload=fresh, retry_at=0.0, error=None)
        return fresh


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def _base_url(self):
        configured = os.environ.get("SITE_URL", "").rstrip("/")
        if configured:
            return configured
        host = self.headers.get("Host", "localhost")
        proto = self.headers.get("X-Forwarded-Proto") or ("http" if host.startswith(("localhost", "127.")) else "https")
        return f"{proto}://{host}"

    def _send_html(self, status, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _fallback_page(self, title, message, path, base):
        return pages.layout(title, message, f'<section class="prose"><h2>{title}</h2><p>{message}</p></section>',
                            path, base, "", title, "")

    def do_GET(self):
        path = self.path.split("?")[0]
        base = self._base_url()

        if path == "/robots.txt":
            body = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path in ("/api/bracket",):
            try:
                self._send_json(get_payload())
            except Exception as e:  # noqa: BLE001
                self._send_json({"ok": False, "error": str(e)}, status=502)
            return

        if path == "/sitemap.xml" or pages.is_page(path) or pages_en.is_page(path):
            try:
                payload = get_payload()
            except Exception:
                self._send_html(503, self._fallback_page("잠시 후 다시 시도해 주세요", "대진 데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.", path, base))
                return
            if path == "/sitemap.xml":
                body = pages.sitemap(base, payload, extra_urls=pages_en.sitemap_urls(payload)).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/xml; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            result = pages_en.render(path, base, payload) if pages_en.is_page(path) else pages.render(path, base, payload)
            if result is None or result[1] is None:
                self._send_html(404, self._fallback_page("페이지를 찾을 수 없어요", "주소를 다시 확인해 주세요.", path, base))
                return
            self._send_html(*result)
            return

        super().do_GET()

    def log_message(self, format, *args):
        pass


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"MLB 포스트시즌 대진표 서버 시작: http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
