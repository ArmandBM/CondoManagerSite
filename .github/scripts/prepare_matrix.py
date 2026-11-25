#!/usr/bin/env python3
"""Validate Codex's JSON findings and expose a safe dynamic GitHub matrix."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

REQUIRED = (
    "title",
    "category",
    "severity",
    "file",
    "line",
    "description",
    "impact",
    "remediation",
    "sqale_rule",
    "estimated_minutes",
    "validation",
)
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: prepare_matrix.py path/to/debts.json")
    path = Path(sys.argv[1])
    if not path.is_file():
        fail(f"Codex did not create the required file: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON from Codex: {exc}")

    debts = payload.get("debts") if isinstance(payload, dict) else None
    if not isinstance(debts, list):
        fail("Expected a JSON object with a 'debts' array")

    max_debts = int(os.environ.get("MAX_DEBTS", "3"))
    if len(debts) > max_debts:
        fail(f"Codex returned {len(debts)} debts; maximum allowed is {max_debts}")

    repo_root = Path.cwd().resolve()
    safe_debts = []
    seen = set()
    for index, item in enumerate(debts, start=1):
        if not isinstance(item, dict):
            fail(f"Debt #{index} is not a JSON object")
        missing = [field for field in REQUIRED if field not in item]
        if missing:
            fail(f"Debt #{index} is missing fields: {', '.join(missing)}")

        rel = PurePosixPath(str(item["file"]))
        if rel.is_absolute() or ".." in rel.parts:
            fail(f"Debt #{index} contains an unsafe file path")
        source = (repo_root / Path(*rel.parts)).resolve()
        if repo_root not in source.parents or not source.is_file():
            fail(f"Debt #{index} points to a file that does not exist in the repository: {rel}")

        try:
            line = int(item["line"])
            minutes = int(item["estimated_minutes"])
        except (TypeError, ValueError):
            fail(f"Debt #{index}: line and estimated_minutes must be integers")
        if line < 1 or minutes < 0:
            fail(f"Debt #{index}: line must be >= 1 and estimated_minutes must be >= 0")

        severity = str(item["severity"]).lower()
        if severity not in ALLOWED_SEVERITIES:
            fail(f"Debt #{index}: unsupported severity {severity!r}")

        # Stable ID helps reruns update the same PR branch instead of duplicating it.
        identity = "|".join(
            [
                str(item.get("sonar_issue_key", "")),
                str(rel),
                str(item["sqale_rule"]),
                str(item["title"]).strip().lower(),
            ]
        )
        debt_id = "TD-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:10]
        if debt_id in seen:
            continue
        seen.add(debt_id)

        safe_item = {key: item[key] for key in REQUIRED}
        safe_item.update({"id": debt_id, "file": str(rel), "line": line, "estimated_minutes": minutes, "severity": severity})
        safe_debts.append(safe_item)

    has_debts = bool(safe_debts)
    # An empty matrix is invalid in Actions; use a skipped sentinel job instead.
    matrix_items = safe_debts or [{"id": "NO-DEBTS"}]
    matrix = {"include": matrix_items}
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        fail("GITHUB_OUTPUT is not set")
    with open(output_path, "a", encoding="utf-8") as output:
        output.write("matrix=" + json.dumps(matrix, ensure_ascii=False, separators=(",", ":")) + "\n")
        output.write("has_debts=" + ("true" if has_debts else "false") + "\n")
    print(f"Validated {len(safe_debts)} actionable debts")


if __name__ == "__main__":
    main()
