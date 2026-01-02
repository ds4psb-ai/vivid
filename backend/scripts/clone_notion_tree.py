import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from notion_client import Client


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "notion_clone"

META_KEYS = {
    "object",
    "id",
    "created_time",
    "last_edited_time",
    "created_by",
    "last_edited_by",
    "parent",
    "archived",
    "has_children",
    "in_trash",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clone a Notion page tree into another Notion workspace."
    )
    parser.add_argument("--source-page-id", help="Source page ID (32 hex or UUID).")
    parser.add_argument("--source-page-url", help="Source page URL.")
    parser.add_argument("--target-parent-id", help="Target parent page ID.")
    parser.add_argument("--target-parent-url", help="Target parent page URL.")
    parser.add_argument("--source-token", help="Notion token for source workspace.")
    parser.add_argument("--target-token", help="Notion token for target workspace.")
    parser.add_argument(
        "--follow-links",
        action="store_true",
        help="Follow link_to_page blocks when possible.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Sleep seconds between API calls.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=0,
        help="Stop after cloning N pages (0 = no limit).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to store clone reports.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Skip writes.")
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sleep(delay: float) -> None:
    if delay > 0:
        time.sleep(delay)


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


def _resolve_source_page_id(args: argparse.Namespace) -> Optional[str]:
    for value in (
        args.source_page_id,
        args.source_page_url,
        os.getenv("NOTION_SOURCE_PAGE_ID"),
        os.getenv("NOTION_SOURCE_PAGE_URL"),
    ):
        page_id = _normalize_page_id(value)
        if page_id:
            return page_id
    return None


def _resolve_target_parent_id(args: argparse.Namespace) -> Optional[str]:
    for value in (
        args.target_parent_id,
        args.target_parent_url,
        os.getenv("NOTION_TARGET_PARENT_ID"),
        os.getenv("NOTION_TARGET_PARENT_URL"),
    ):
        page_id = _normalize_page_id(value)
        if page_id:
            return page_id
    return None


def _resolve_token(args: argparse.Namespace, key: str, fallback_keys: List[str]) -> Optional[str]:
    if key == "source" and args.source_token:
        return args.source_token
    if key == "target" and args.target_token:
        return args.target_token
    for env_key in fallback_keys:
        token = os.getenv(env_key)
        if token:
            return token
    return None


def _extract_title(page: Dict[str, Any]) -> str:
    properties = page.get("properties") or {}
    for prop in properties.values():
        if prop.get("type") == "title":
            pieces = prop.get("title") or []
            title = "".join(part.get("plain_text", "") for part in pieces).strip()
            return title or "Untitled"
    return "Untitled"


def _extract_database_title(database: Dict[str, Any]) -> str:
    pieces = database.get("title") or []
    title = "".join(part.get("plain_text", "") for part in pieces).strip()
    return title or "Untitled Database"


def _clean_block_payload(block: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    block_type = block.get("type")
    if not block_type:
        return None
    if block_type in {"child_page", "child_database"}:
        return None

    data = block.get(block_type)
    if not isinstance(data, dict):
        return None

    cleaned = {k: v for k, v in data.items() if k not in META_KEYS}
    if block_type in {"image", "video", "file", "audio", "pdf"}:
        file_info = cleaned.get("file")
        if isinstance(file_info, dict) and file_info.get("url"):
            cleaned.pop("file", None)
            cleaned["external"] = {"url": file_info["url"]}
    return {"object": "block", "type": block_type, block_type: cleaned}


def _paragraph_fallback(text: str) -> Dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": text}},
            ]
        },
    }


def _list_block_children(
    client: Client, block_id: str, delay: float
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    while True:
        response = client.blocks.children.list(block_id=block_id, start_cursor=cursor)
        results.extend(response.get("results") or [])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
        _sleep(delay)
    return results


def _query_database_pages(
    client: Client, database_id: str, delay: float
) -> Iterable[str]:
    cursor: Optional[str] = None
    while True:
        response = client.databases.query(
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


def _create_page(
    client: Client, parent_id: str, title: str, dry_run: bool
) -> Optional[Dict[str, Any]]:
    payload = {
        "parent": {"type": "page_id", "page_id": parent_id},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        },
    }
    if dry_run:
        return {"id": f"dry-run-{parent_id[:8]}", "properties": payload["properties"]}
    return client.pages.create(**payload)


def _append_block(
    client: Client, target_block_id: str, payload: Dict[str, Any], dry_run: bool
) -> Optional[str]:
    if dry_run:
        return f"dry-run-{target_block_id[:8]}"
    response = client.blocks.children.append(block_id=target_block_id, children=[payload])
    results = response.get("results") or []
    if not results:
        return None
    return results[0].get("id")


def _clone_blocks(
    source: Client,
    target: Client,
    source_block_id: str,
    target_block_id: str,
    page_map: Dict[str, str],
    errors: List[str],
    follow_links: bool,
    delay: float,
    dry_run: bool,
) -> None:
    blocks = _list_block_children(source, source_block_id, delay)
    for block in blocks:
        block_type = block.get("type")
        if block_type == "child_page":
            child_id = block.get("id")
            if child_id:
                _clone_page_tree(
                    source,
                    target,
                    child_id,
                    target_block_id,
                    page_map,
                    errors,
                    follow_links,
                    delay,
                    dry_run,
                )
            continue
        if block_type == "child_database":
            db_id = block.get("id")
            if db_id:
                _clone_database(
                    source,
                    target,
                    db_id,
                    target_block_id,
                    page_map,
                    errors,
                    follow_links,
                    delay,
                    dry_run,
                )
            continue
        if block_type == "link_to_page" and follow_links:
            link = block.get("link_to_page") or {}
            link_page_id = link.get("page_id")
            if link_page_id:
                _clone_page_tree(
                    source,
                    target,
                    link_page_id,
                    target_block_id,
                    page_map,
                    errors,
                    follow_links,
                    delay,
                    dry_run,
                )
            continue

        payload = _clean_block_payload(block)
        if not payload:
            payload = _paragraph_fallback(f"[Unsupported block: {block_type}]")

        try:
            new_block_id = _append_block(target, target_block_id, payload, dry_run)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Failed to append block {block.get('id')} ({block_type}): {exc}")
            continue

        if block.get("has_children") and new_block_id:
            _clone_blocks(
                source,
                target,
                block["id"],
                new_block_id,
                page_map,
                errors,
                follow_links,
                delay,
                dry_run,
            )
        _sleep(delay)


def _clone_database(
    source: Client,
    target: Client,
    database_id: str,
    target_parent_id: str,
    page_map: Dict[str, str],
    errors: List[str],
    follow_links: bool,
    delay: float,
    dry_run: bool,
) -> None:
    try:
        database = source.databases.retrieve(database_id=database_id)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to retrieve database {database_id}: {exc}")
        return

    title = _extract_database_title(database)
    placeholder_title = f"{title} (Database)"
    created = _create_page(target, target_parent_id, placeholder_title, dry_run)
    if not created:
        errors.append(f"Failed to create placeholder page for database {database_id}")
        return

    target_page_id = created["id"]
    page_map[database_id] = target_page_id

    for page_id in _query_database_pages(source, database_id, delay):
        _clone_page_tree(
            source,
            target,
            page_id,
            target_page_id,
            page_map,
            errors,
            follow_links,
            delay,
            dry_run,
        )


def _clone_page_tree(
    source: Client,
    target: Client,
    source_page_id: str,
    target_parent_id: str,
    page_map: Dict[str, str],
    errors: List[str],
    follow_links: bool,
    delay: float,
    dry_run: bool,
) -> None:
    if source_page_id in page_map:
        return
    try:
        page = source.pages.retrieve(page_id=source_page_id)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to retrieve page {source_page_id}: {exc}")
        return

    title = _extract_title(page)
    try:
        created = _create_page(target, target_parent_id, title, dry_run)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to create page for {source_page_id}: {exc}")
        return

    if not created:
        errors.append(f"Failed to create page for {source_page_id}")
        return

    target_page_id = created["id"]
    page_map[source_page_id] = target_page_id

    _clone_blocks(
        source,
        target,
        source_page_id,
        target_page_id,
        page_map,
        errors,
        follow_links,
        delay,
        dry_run,
    )


def _write_report(output_dir: Path, page_map: Dict[str, str], errors: List[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "cloned_at": _now_iso(),
        "page_count": len(page_map),
        "page_map": page_map,
        "errors": errors,
    }
    (output_dir / "clone_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    args = _parse_args()
    source_page_id = _resolve_source_page_id(args)
    target_parent_id = _resolve_target_parent_id(args)
    if not source_page_id or not target_parent_id:
        print("Missing source page ID or target parent page ID.")
        raise SystemExit(1)

    source_token = _resolve_token(
        args,
        "source",
        ["NOTION_SOURCE_TOKEN", "NOTION_TOKEN", "NOTION_API_KEY", "NOTION_SECRET"],
    )
    target_token = _resolve_token(
        args,
        "target",
        ["NOTION_TARGET_TOKEN", "NOTION_TOKEN", "NOTION_API_KEY", "NOTION_SECRET"],
    )
    if not source_token or not target_token:
        print("Missing Notion tokens for source/target workspaces.")
        raise SystemExit(1)

    source = Client(auth=source_token)
    target = Client(auth=target_token)

    page_map: Dict[str, str] = {}
    errors: List[str] = []

    _clone_page_tree(
        source,
        target,
        source_page_id,
        target_parent_id,
        page_map,
        errors,
        args.follow_links,
        args.sleep,
        args.dry_run,
    )

    if args.max_pages and len(page_map) > args.max_pages:
        page_map = dict(list(page_map.items())[: args.max_pages])

    output_dir = Path(args.output_dir).expanduser().resolve()
    _write_report(output_dir, page_map, errors)

    print(f"Cloned {len(page_map)} page(s). Report saved to {output_dir / 'clone_report.json'}")
    if errors:
        print(f"Encountered {len(errors)} error(s). See clone_report.json.")


if __name__ == "__main__":
    main()
