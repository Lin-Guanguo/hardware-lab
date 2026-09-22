#!/usr/bin/env python3
"""Validate the safety invariants of the E14 pre-manufacturing snapshot."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
DEFAULT_GATES = PROJECT / "hardware" / "pcb-e14-manufacturing-gates.json"
DEFAULT_LAYOUT = PROJECT / "hardware" / "pcb-e14-battery-layout.json"
DEFAULT_PROJECT = REPO / "eda" / "NFC-Business-Card-84x52-E14-Battery-Layout.eprj2"


def fail(message):
    raise SystemExit(f"error: {message}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gates", type=Path, default=DEFAULT_GATES)
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    args = parser.parse_args()

    gates = json.loads(args.gates.read_text())
    layout_document = json.loads(args.layout.read_text())
    layout = layout_document.get("result", layout_document)
    if gates.get("layout") != "E14":
        fail("gate record is not for E14")
    if layout.get("status") != "PRIMARY_LAYOUT_CANDIDATE_NOT_MANUFACTURING_READY":
        fail("layout report status changed unexpectedly")
    if layout.get("boardSizeMm") != [84, 52]:
        fail(f"unexpected board size: {layout.get('boardSizeMm')}")
    if layout.get("copperLineCount") != 0 or layout.get("viaCount") != 0:
        fail("snapshot is no longer the documented zero-copper E14 baseline")
    if not args.project.is_file():
        fail(f"EDA project not found: {args.project}")
    project_hash = hashlib.sha256(args.project.read_bytes()).hexdigest()
    expected_hash = gates.get("source", {}).get("eda_project_sha256")
    if expected_hash and project_hash != expected_hash:
        fail("EDA project hash differs; refresh the gate record after an intentional revision")
    with sqlite3.connect(args.project) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
    if quick_check != "ok":
        fail(f"SQLite quick_check returned {quick_check!r}")
    release = gates.get("release_artifacts", {})
    if any(release.values()):
        fail("a release artifact is marked as generated before all gates pass")
    enclosure_gate = next((gate for gate in gates.get("gates", [])
                           if gate.get("id") == "cad-printable-enclosure"), None)
    if enclosure_gate and enclosure_gate.get("test_candidate"):
        candidate = (args.gates.parent / enclosure_gate["test_candidate"]).resolve()
        if not candidate.is_file():
            fail(f"documented enclosure test candidate not found: {candidate}")
    blocked = [gate["id"] for gate in gates.get("gates", []) if gate.get("status") in {"BLOCKED", "BLOCKED_INPUT", "BLOCKED_DEPENDENCY", "NOT_STARTED"}]
    result = {
        "ok": True,
        "layout": "E14",
        "status": gates.get("status"),
        "blocked_gates": blocked,
        "project_sha256": project_hash,
        "sqlite_quick_check": quick_check,
        "release_artifacts": release,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
