#!/usr/bin/env python3
"""Wait for the submitted Sonar analysis and export unresolved project issues."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

PAGE_SIZE = 500
WAIT_SECONDS = 300


def read_properties(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit(f"Sonar report file not found: {path}")
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--report-task", default=".scannerwork/report-task.txt")
    args = parser.parse_args()

    token = os.environ.get("SONAR_TOKEN")
    project_key = os.environ.get("SONAR_PROJECT_KEY")
    base_url = (os.environ.get("SONAR_URL") or "https://sonarcloud.io").rstrip("/")
    if not token or not project_key:
        raise SystemExit("SONAR_TOKEN and SONAR_PROJECT_KEY must be configured")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})

    properties = read_properties(Path(args.report_task))
    task_url = properties.get("ceTaskUrl")
    if task_url:
        deadline = time.monotonic() + WAIT_SECONDS
        while True:
            response = session.get(task_url, timeout=30)
            response.raise_for_status()
            task = response.json().get("task", {})
            status = task.get("status")
            if status == "SUCCESS":
                break
            if status in {"FAILED", "CANCELED"}:
                raise SystemExit(f"SonarQube background task ended with status {status}")
            if time.monotonic() >= deadline:
                raise SystemExit("Timed out waiting for SonarQube analysis to finish")
            time.sleep(3)

    issues: list[dict] = []
    page = 1
    total = None
    while total is None or len(issues) < total:
        response = session.get(
            f"{base_url}/api/issues/search",
            params={
                "componentKeys": project_key,
                "resolved": "false",
                "p": page,
                "ps": PAGE_SIZE,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload.get("issues", [])
        issues.extend(batch)
        total = int(payload.get("total", len(issues)))
        if not batch:
            break
        page += 1

    selected_fields = (
        "key",
        "rule",
        "component",
        "project",
        "line",
        "message",
        "effort",
        "severity",
        "type",
        "status",
        "tags",
    )
    normalized = [
        {key: issue.get(key) for key in selected_fields if key in issue}
        for issue in issues
    ]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"total": len(normalized), "issues": normalized}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(normalized)} unresolved SonarQube issues to {output}")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"SonarQube API request failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
