#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

JSONValue = Any


@dataclass
class CheckResult:
    rule_id: str
    severity: str
    status: str
    message: str
    details: Dict[str, Any]


def _is_non_empty(value: JSONValue) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def _split_path(path: str) -> List[str]:
    return path.split(".") if path else []


def _extract_values(root: JSONValue, path: str) -> List[JSONValue]:
    if path.endswith(".start_sec_end_sec"):
        base_path = path[: -len(".start_sec_end_sec")]
        pairs: List[List[float]] = []
        for obj in _extract_values(root, base_path):
            if isinstance(obj, dict):
                start = obj.get("start_sec")
                end = obj.get("end_sec")
                if start is not None and end is not None:
                    pairs.append([start, end])
        return pairs
    if path.endswith(".start_ms_end_ms"):
        base_path = path[: -len(".start_ms_end_ms")]
        pairs: List[List[float]] = []
        for obj in _extract_values(root, base_path):
            if isinstance(obj, dict):
                start = obj.get("start_ms")
                end = obj.get("end_ms")
                if start is not None and end is not None:
                    pairs.append([start, end])
        return pairs

    segments = _split_path(path)

    def walk(obj: JSONValue, idx: int) -> List[JSONValue]:
        if idx >= len(segments):
            return [obj]
        segment = segments[idx]
        is_list = segment.endswith("[]")
        key = segment[:-2] if is_list else segment

        if key:
            if not isinstance(obj, dict) or key not in obj:
                return []
            obj = obj[key]

        if is_list:
            if not isinstance(obj, list):
                return []
            values: List[JSONValue] = []
            for item in obj:
                values.extend(walk(item, idx + 1))
            return values
        return walk(obj, idx + 1)

    return walk(root, 0)


def _extract_list(root: JSONValue, path: str, fallback_paths: Optional[List[str]]) -> List[JSONValue]:
    values = _extract_values(root, path)
    if not values and fallback_paths:
        for fallback in fallback_paths:
            values = _extract_values(root, fallback)
            if values:
                break
    if len(values) == 1 and isinstance(values[0], list):
        return values[0]
    if all(isinstance(v, dict) for v in values):
        return values
    return []


def _extract_first_value(root: JSONValue, path: str) -> Optional[JSONValue]:
    values = _extract_values(root, path)
    return values[0] if values else None


def _extract_values_with_fallback(
    root: JSONValue, path: str, fallback_paths: Optional[List[str]]
) -> List[JSONValue]:
    values = _extract_values(root, path)
    if not values and fallback_paths:
        for fallback in fallback_paths:
            values = _extract_values(root, fallback)
            if values:
                break
    return values


def _condition_single(root: JSONValue, condition: Dict[str, Any]) -> bool:
    if "any_of" in condition:
        return any(_condition_single(root, sub) for sub in condition["any_of"])

    cond_path = condition.get("path", "")
    if "exists" in condition:
        values = _extract_values(root, cond_path)
        exists = any(_is_non_empty(v) for v in values)
        return exists is condition["exists"]

    cond_value = _extract_first_value(root, cond_path)
    if cond_value is None:
        return False
    if "in" in condition:
        return cond_value in condition["in"]
    if "equals" in condition:
        return cond_value == condition["equals"]
    return True


def _conditions_met(root: JSONValue, conditions: Optional[List[Dict[str, Any]]]) -> bool:
    if not conditions:
        return True
    for condition in conditions:
        if not _condition_single(root, condition):
            return False
    return True


def _check_requires_any_non_empty(root: JSONValue, paths: List[str]) -> Tuple[bool, Dict[str, Any]]:
    for path in paths:
        values = _extract_values(root, path)
        if any(_is_non_empty(v) for v in values):
            return True, {"matched_path": path}
    return False, {"checked_paths": paths}


def _check_requires_non_empty(root: JSONValue, path: str) -> Tuple[bool, Dict[str, Any]]:
    values = _extract_values(root, path)
    return any(_is_non_empty(v) for v in values), {"path": path, "values_found": len(values)}


def _check_for_each_required_fields(
    root: JSONValue,
    path: str,
    fallback_paths: Optional[List[str]],
    required_fields: List[str],
) -> Tuple[bool, Dict[str, Any]]:
    items = _extract_list(root, path, fallback_paths)
    if not items:
        return False, {"path": path, "reason": "no_items"}
    missing: List[Dict[str, Any]] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            missing.append({"index": idx, "missing": required_fields})
            continue
        missing_fields = [
            field
            for field in required_fields
            if field not in item or item.get(field) in (None, "")
        ]
        if missing_fields:
            missing.append({"index": idx, "missing": missing_fields})
    return len(missing) == 0, {"missing": missing}


def _check_for_each_array_item(
    root: JSONValue,
    path: str,
    fallback_paths: Optional[List[str]],
    checks: List[Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
    items = _extract_list(root, path, fallback_paths)
    if not items:
        return False, {"path": path, "reason": "no_items"}
    failures: List[Dict[str, Any]] = []
    for idx, item in enumerate(items):
        for check in checks:
            check_type = check.get("type")
            optional = check.get("optional", False)
            check_path = check.get("path", "")
            values = _extract_values(item, check_path)
            if check_type == "requires_non_empty":
                ok = any(_is_non_empty(v) for v in values)
                if not ok and not optional:
                    failures.append({"index": idx, "check": check_type, "path": check_path})
            elif check_type == "length_equals":
                target = check.get("value")
                if not values and optional:
                    continue
                for value in values:
                    if not isinstance(value, list) or len(value) != target:
                        failures.append(
                            {
                                "index": idx,
                                "check": check_type,
                                "path": check_path,
                                "expected": target,
                                "actual": len(value) if isinstance(value, list) else None,
                            }
                        )
                        break
            elif check_type == "value_range":
                min_val = check.get("min")
                max_val = check.get("max")
                for value in values:
                    if isinstance(value, (int, float)):
                        if (min_val is not None and value < min_val) or (
                            max_val is not None and value > max_val
                        ):
                            failures.append(
                                {
                                    "index": idx,
                                    "check": check_type,
                                    "path": check_path,
                                    "value": value,
                                    "range": [min_val, max_val],
                                }
                            )
                    elif not optional:
                        failures.append(
                            {
                                "index": idx,
                                "check": check_type,
                                "path": check_path,
                                "value": value,
                                "range": [min_val, max_val],
                            }
                        )
            elif check_type == "ordered_pair":
                if not values and optional:
                    continue
                for value in values:
                    if not isinstance(value, list) or len(value) != 2:
                        failures.append({"index": idx, "check": check_type, "path": check_path})
                        continue
                    start, end = value
                    if start is None or end is None or start > end:
                        failures.append(
                            {
                                "index": idx,
                                "check": check_type,
                                "path": check_path,
                                "value": value,
                            }
                        )
            else:
                failures.append({"index": idx, "check": check_type, "path": check_path})
    return len(failures) == 0, {"failures": failures}


def _check_value_range(
    root: JSONValue,
    path: str,
    min_val: float,
    max_val: float,
    fallback_paths: Optional[List[str]],
) -> Tuple[bool, Dict[str, Any]]:
    values = _extract_values_with_fallback(root, path, fallback_paths)
    violations = [v for v in values if isinstance(v, (int, float)) and (v < min_val or v > max_val)]
    return len(violations) == 0, {"violations": violations}


def _check_length_equals(
    root: JSONValue,
    path: str,
    length: int,
    fallback_paths: Optional[List[str]],
) -> Tuple[bool, Dict[str, Any]]:
    values = _extract_values_with_fallback(root, path, fallback_paths)
    violations = [
        v for v in values if not isinstance(v, list) or len(v) != length
    ]
    return len(violations) == 0, {"violations": violations}


def _check_unique(root: JSONValue, path: str) -> Tuple[bool, Dict[str, Any]]:
    values = [v for v in _extract_values(root, path) if v is not None]
    seen = set()
    duplicates = []
    for value in values:
        if value in seen:
            duplicates.append(value)
        seen.add(value)
    return len(duplicates) == 0, {"duplicates": duplicates}


def _check_ordered_pair(
    root: JSONValue, path: str, fallback_paths: Optional[List[str]]
) -> Tuple[bool, Dict[str, Any]]:
    values = _extract_values_with_fallback(root, path, fallback_paths)
    failures = []
    for value in values:
        if not isinstance(value, list) or len(value) != 2:
            failures.append(value)
            continue
        start, end = value
        if start is None or end is None or start > end:
            failures.append(value)
    return len(failures) == 0, {"violations": failures}


def _check_is_not_list(
    root: JSONValue, path: str, fallback_paths: Optional[List[str]]
) -> Tuple[bool, Dict[str, Any]]:
    values = _extract_values_with_fallback(root, path, fallback_paths)
    value = values[0] if values else None
    return not isinstance(value, list), {"value_type": type(value).__name__}


def _evaluate_rule(root: JSONValue, rule: Dict[str, Any]) -> CheckResult:
    rule_id = rule.get("id", "unknown")
    severity = rule.get("severity", "warn")
    message = rule.get("message", "")
    check_type = rule.get("check_type")

    if not _conditions_met(root, rule.get("conditions")):
        return CheckResult(rule_id=rule_id, severity=severity, status="skip", message=message, details={})

    details: Dict[str, Any] = {}
    passed = False

    if check_type == "requires_any_non_empty":
        passed, details = _check_requires_any_non_empty(root, rule.get("paths", []))
    elif check_type == "requires_non_empty":
        passed, details = _check_requires_non_empty(root, rule.get("path", ""))
    elif check_type == "for_each_required_fields":
        passed, details = _check_for_each_required_fields(
            root,
            rule.get("path", ""),
            rule.get("fallback_paths"),
            rule.get("required_fields", []),
        )
    elif check_type == "for_each_array_item":
        passed, details = _check_for_each_array_item(
            root,
            rule.get("path", ""),
            rule.get("fallback_paths"),
            rule.get("checks", []),
        )
    elif check_type == "value_range":
        passed, details = _check_value_range(
            root,
            rule.get("path", ""),
            rule.get("min", 0),
            rule.get("max", 1),
            rule.get("fallback_paths"),
        )
    elif check_type == "length_equals":
        passed, details = _check_length_equals(
            root, rule.get("path", ""), rule.get("value", 0), rule.get("fallback_paths")
        )
    elif check_type == "unique":
        passed, details = _check_unique(root, rule.get("path", ""))
    elif check_type == "ordered_pair":
        passed, details = _check_ordered_pair(root, rule.get("path", ""), rule.get("fallback_paths"))
    elif check_type == "is_not_list":
        passed, details = _check_is_not_list(root, rule.get("path", ""), rule.get("fallback_paths"))
    else:
        return CheckResult(
            rule_id=rule_id,
            severity=severity,
            status="skip",
            message=f"Unknown check_type: {check_type}",
            details={},
        )

    status = "pass" if passed else "fail"
    return CheckResult(rule_id=rule_id, severity=severity, status=status, message=message, details=details)


async def _read_json(path: str) -> JSONValue:
    def read_sync() -> JSONValue:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    return await asyncio.to_thread(read_sync)


def _resolve_analysis_root(data: JSONValue, root_key: str) -> JSONValue:
    if isinstance(data, dict) and root_key in data and isinstance(data[root_key], dict):
        return data[root_key]
    return data


def _summarize(results: List[CheckResult]) -> Dict[str, int]:
    summary = {"pass": 0, "fail": 0, "skip": 0, "warn_fail": 0, "error_fail": 0}
    for result in results:
        summary[result.status] += 1
        if result.status == "fail":
            if result.severity == "error":
                summary["error_fail"] += 1
            else:
                summary["warn_fail"] += 1
    return summary


def _print_report(results: List[CheckResult]) -> None:
    for result in results:
        if result.status == "pass":
            continue
        detail = json.dumps(result.details, ensure_ascii=True)
        print(f"{result.rule_id} [{result.severity}] {result.status}: {result.message} {detail}")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Validate VDG analysis JSON against SSOT rules.")
    parser.add_argument("--analysis", required=True, help="Path to analysis JSON file.")
    parser.add_argument(
        "--rules",
        default=str(Path("docs") / "vdg-ssot-checks.json"),
        help="Path to SSOT rules JSON file.",
    )
    parser.add_argument("--analysis-root", default=None, help="Root key for analysis in input.")
    parser.add_argument("--format", default="text", choices=["text", "json"], help="Output format.")
    parser.add_argument("--fail-on-warn", action="store_true", help="Treat warnings as failures.")

    args = parser.parse_args()

    try:
        rules_doc = await _read_json(args.rules)
        analysis_doc = await _read_json(args.analysis)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to read inputs: {exc}", file=sys.stderr)
        return 2

    rules_scope = rules_doc.get("scope", {}) if isinstance(rules_doc, dict) else {}
    root_key = args.analysis_root or rules_scope.get("analysis_root") or "analysis"
    analysis_root = _resolve_analysis_root(analysis_doc, root_key)
    rules = rules_doc.get("rules", [])

    results = [_evaluate_rule(analysis_root, rule) for rule in rules]
    summary = _summarize(results)

    if args.format == "json":
        payload = {
            "summary": summary,
            "results": [result.__dict__ for result in results],
        }
        print(json.dumps(payload, indent=2))
    else:
        _print_report(results)
        print(
            f"Summary: pass={summary['pass']} fail={summary['fail']} skip={summary['skip']} "
            f"error_fail={summary['error_fail']} warn_fail={summary['warn_fail']}"
        )

    if summary["error_fail"] > 0:
        return 2
    if summary["warn_fail"] > 0 and args.fail_on_warn:
        return 1
    if summary["warn_fail"] > 0:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
