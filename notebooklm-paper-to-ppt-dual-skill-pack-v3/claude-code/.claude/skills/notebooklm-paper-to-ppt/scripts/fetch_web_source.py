#!/usr/bin/env python3
"""Fetch a single webpage and extract readable body text for notes generation."""
from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SEC = 30
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; notebooklm-paper-to-ppt/1.0)"
BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}
SKIP_TAGS = {"form", "header", "nav", "footer", "noscript", "script", "style", "svg"}
BLOCKED_MARKERS = (
    "access denied",
    "captcha",
    "enable javascript",
    "log in",
    "login",
    "sign in",
)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    compact = "\n".join(line for line in lines if line)
    compact = re.sub(r"\n{3,}", "\n\n", compact).strip()
    return compact


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []
        self._title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in SKIP_TAGS:
            self._skip_depth += 1
            return
        if lowered == "title":
            self._in_title = True
            return
        if self._skip_depth == 0 and lowered in BLOCK_TAGS and self._parts and self._parts[-1] != "\n":
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if lowered == "title":
            self._in_title = False
            return
        if self._skip_depth == 0 and lowered in BLOCK_TAGS and self._parts and self._parts[-1] != "\n":
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        if self._skip_depth > 0:
            return
        if data.strip():
            self._parts.append(data)

    def text(self) -> str:
        return normalize_text("".join(self._parts))

    def title(self) -> str:
        return normalize_text("".join(self._title_parts))


def fetch_html(url: str, timeout_sec: int) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https", "file"}:
        raise RuntimeError(f"Unsupported URL scheme for webpage fetch: {parsed.scheme or '(missing)'}")
    if parsed.scheme == "file":
        file_path = Path(unquote(parsed.path))
        return file_path.read_text(encoding="utf-8")

    request = Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with urlopen(request, timeout=timeout_sec) as response:
            status = getattr(response, "status", None)
            if status not in (None, 200):
                raise RuntimeError(f"Expected HTTP 200, got {status} for {url}")
            charset = response.headers.get_content_charset() or "utf-8"
            payload = response.read()
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while fetching {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc.reason}") from exc
    return payload.decode(charset, errors="replace")


def try_trafilatura_extract(html: str, url: str) -> str | None:
    try:
        import trafilatura
    except ModuleNotFoundError:
        return None
    extracted = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_links=False,
        include_tables=True,
        output_format="txt",
    )
    if extracted is None:
        return None
    return normalize_text(extracted)


def fallback_extract(html: str) -> tuple[str, str]:
    parser = VisibleTextParser()
    parser.feed(html)
    parser.close()
    return (parser.title(), parser.text())


def looks_blocked(text: str) -> bool:
    lowered = text.lower()
    if not lowered:
        return True
    if len(lowered) < 200 and any(marker in lowered for marker in BLOCKED_MARKERS):
        return True
    return False


def build_output_text(url: str, title: str, body: str) -> str:
    parsed = urlparse(url)
    header = [
        f"Source URL: {url}",
        f"Source Host: {parsed.netloc}",
    ]
    if title:
        header.append(f"Page Title: {title}")
    header.append("")
    header.append(body)
    return "\n".join(header).strip() + "\n"


def extract_webpage_text(url: str, timeout_sec: int) -> tuple[str, str]:
    html = fetch_html(url, timeout_sec)
    extracted = try_trafilatura_extract(html, url)
    title, fallback_text = fallback_extract(html)
    body = extracted or fallback_text
    if looks_blocked(body):
        raise RuntimeError(f"Fetched page from {url} but did not obtain usable body text.")
    return (title, body)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch one webpage and extract readable body text.")
    parser.add_argument("--url", required=True, help="HTTP(S) URL to fetch; file:// is supported for local fixtures")
    parser.add_argument("--output", required=True, help="Path to write extracted UTF-8 text")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC, help="HTTP timeout seconds")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    output_path = Path(args.output)
    try:
        title, body = extract_webpage_text(args.url, args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_output_text(args.url, title, body), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
