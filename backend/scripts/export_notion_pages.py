import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from notion_client import Client
from notion_to_md import NotionToMarkdown


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "notion_export"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a Notion page tree to Markdown with an index report."
    )
    parser.add_argument("--page-id", help="Root Notion page ID (32 hex or UUID).")
    parser.add_argument("--page-url", help="Root Notion page URL.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory for markdown and index/report files.",
    )
    parser.add_argument(
        "--follow-links",
        action="store_true",
        help="Follow link_to_page blocks in addition to child pages/databases.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=0,
        help="Stop after exporting N pages (0 = no limit).",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Sleep seconds between API calls to reduce rate limiting.",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save raw page JSON alongside markdown files.",
    )
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_page_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    dashed = re.search(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        text,
    )
    if dashed:
        return dashed.group(0)
    raw = re.search(r"[0-9a-fA-F]{32}", text)
    if raw:
        clean = raw.group(0)
        return f"{clean[:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:]}"
    return None


def _notion_page_url(page_id: str) -> str:
    return f"https://www.notion.so/{page_id.replace('-', '')}"


def _extract_title(page: Dict[str, Any]) -> str:
    properties = page.get("properties") or {}
    for prop in properties.values():
        if prop.get("type") == "title":
            pieces = prop.get("title") or []
            title = "".join(part.get("plain_text", "") for part in pieces).strip()
            return title or "Untitled"
    return "Untitled"


def _slugify(title: str, fallback: str) -> str:
    ascii_title = title.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_title).strip("-").lower()
    return cleaned or fallback


def _sleep(delay: float) -> None:
    if delay > 0:
        time.sleep(delay)


def _list_block_children(
    notion: Client, block_id: str, delay: float
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    while True:
        response = notion.blocks.children.list(block_id=block_id, start_cursor=cursor)
        results.extend(response.get("results") or [])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
        _sleep(delay)
    return results


def _iter_blocks_recursive(
    notion: Client, root_block_id: str, delay: float
) -> Iterable[Dict[str, Any]]:
    queue: List[str] = [root_block_id]
    seen: Set[str] = set()
    while queue:
        block_id = queue.pop(0)
        if block_id in seen:
            continue
        seen.add(block_id)
        children = _list_block_children(notion, block_id, delay)
        for block in children:
            yield block
            if block.get("has_children"):
                queue.append(block["id"])


def _query_database_pages(
    notion: Client, database_id: str, delay: float
) -> Iterable[str]:
    cursor: Optional[str] = None
    while True:
        response = notion.databases.query(
            database_id=database_id, start_cursor=cursor, page_size=100
        )
        for page in response.get("results") or []:
            page_id = page.get("id")
            if page_id:
                yield page_id
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
        _sleep(delay)


def _to_markdown(n2m: NotionToMarkdown, page_id: str) -> str:
    md_blocks = n2m.page_to_markdown(page_id)
    result = n2m.to_markdown_string(md_blocks)
    if isinstance(result, dict):
        return result.get("parent", "")
    if isinstance(result, str):
        return result
    return str(result)


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _resolve_root_page_id(args: argparse.Namespace) -> Optional[str]:
    for value in (
        args.page_id,
        args.page_url,
        os.getenv("NOTION_PAGE_ID"),
        os.getenv("NOTION_PAGE_URL"),
    ):
        page_id = _normalize_page_id(value)
        if page_id:
            return page_id
    return None


def _resolve_token() -> Optional[str]:
    for key in ("NOTION_TOKEN", "NOTION_API_KEY", "NOTION_SECRET"):
        token = os.getenv(key)
        if token:
            return token
    return None


def _crawl_pages(
    notion: Client,
    n2m: NotionToMarkdown,
    root_page_id: str,
    output_dir: Path,
    follow_links: bool,
    max_pages: int,
    delay: float,
    save_json: bool,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    queue: List[Tuple[str, Optional[str]]] = [(root_page_id, None)]
    visited: Set[str] = set()
    pages: List[Dict[str, Any]] = []
    errors: List[str] = []

    while queue:
        page_id, parent_id = queue.pop()
        if page_id in visited:
            continue
        visited.add(page_id)

        try:
            page = notion.pages.retrieve(page_id=page_id)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Failed to retrieve page {page_id}: {exc}")
            continue

        title = _extract_title(page)
        short_id = page_id.replace("-", "")[:8]
        slug = _slugify(title, short_id)
        filename = f"{slug}-{short_id}.md"
        md_path = _unique_path(output_dir / filename)

        try:
            md_text = _to_markdown(n2m, page_id)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Failed to convert page {page_id} to markdown: {exc}")
            md_text = ""

        md_path.write_text(md_text, encoding="utf-8")
        if save_json:
            json_path = md_path.with_suffix(".json")
            json_path.write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")

        blocks = list(_iter_blocks_recursive(notion, page_id, delay))
        for block in blocks:
            block_type = block.get("type")
            if block_type == "child_page":
                queue.append((block["id"], page_id))
            elif block_type == "child_database":
                for child_page_id in _query_database_pages(notion, block["id"], delay):
                    queue.append((child_page_id, page_id))
            elif follow_links and block_type == "link_to_page":
                link = block.get("link_to_page") or {}
                linked_page_id = link.get("page_id")
                if linked_page_id:
                    queue.append((linked_page_id, page_id))

        record = {
            "page_id": page_id,
            "title": title,
            "slug": md_path.stem,
            "file": str(md_path.relative_to(output_dir)),
            "url": _notion_page_url(page_id),
            "parent_id": parent_id,
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "block_count": len(blocks),
            "char_count": len(md_text),
            "word_count": len(md_text.split()),
        }
        pages.append(record)

        if max_pages and len(pages) >= max_pages:
            break

        _sleep(delay)

    return pages, errors


def _write_report(output_dir: Path, pages: List[Dict[str, Any]], errors: List[str]) -> None:
    total_chars = sum(page.get("char_count", 0) for page in pages)
    total_words = sum(page.get("word_count", 0) for page in pages)
    total_blocks = sum(page.get("block_count", 0) for page in pages)
    report = {
        "exported_at": _now_iso(),
        "page_count": len(pages),
        "total_chars": total_chars,
        "total_words": total_words,
        "total_blocks": total_blocks,
        "errors": errors,
    }
    (output_dir / "index.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    args = _parse_args()
    token = _resolve_token()
    if not token:
        print("Missing NOTION_TOKEN (or NOTION_API_KEY/NOTION_SECRET).")
        raise SystemExit(1)

    root_page_id = _resolve_root_page_id(args)
    if not root_page_id:
        print("Missing root page ID. Provide --page-id or --page-url.")
        raise SystemExit(1)

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    notion = Client(auth=token)
    n2m = NotionToMarkdown(notion)

    pages, errors = _crawl_pages(
        notion=notion,
        n2m=n2m,
        root_page_id=root_page_id,
        output_dir=output_dir,
        follow_links=args.follow_links,
        max_pages=args.max_pages,
        delay=args.sleep,
        save_json=args.save_json,
    )
    _write_report(output_dir, pages, errors)

    print(f"Exported {len(pages)} page(s) to {output_dir}")
    if errors:
        print(f"Encountered {len(errors)} error(s). See report.json for details.")


if __name__ == "__main__":
    main()
