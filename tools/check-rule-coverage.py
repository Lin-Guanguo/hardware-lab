#!/usr/bin/env python3
"""Cross-check the rule table's coverage claims against the checkers.

docs/pcb-design-rules.md marks each rule as automatically covered, blocked,
manual or not applicable. A rule marked automatic that no checker actually
implements is an overclaim, and an overclaim is worse than a gap: it makes the
board look reviewed when it was not. This guard exists because that happened
once already (BE-001, BE-003, IO-001 and DP-002 were marked automatic while
nothing computed them).

Usage:
    python3 tools/check-rule-coverage.py [--rules DOC] [--checker PATH ...]

Exit status is 0 when no rule is claimed automatic without an implementation.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DOC = REPO / "docs/pcb-design-rules.md"
DEFAULT_CHECKERS = sorted((REPO / "projects").glob("*/scripts/check-*.py"))

RULE_ID = re.compile(r"\b([A-Z]{2}-\d{3})\b")
IMPLEMENTED = re.compile(r'"rule":\s*"([A-Z]{2}-\d{3})"')
AUTOMATIC = "✅"


def claimed_status(path: Path):
    """rule id -> status column from every table row in the rule index."""
    claims = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        ids = RULE_ID.findall(cells[0])
        if not ids:
            continue
        for rule_id in ids:
            claims[rule_id] = cells[2]
    return claims


def implemented_ids(paths):
    found = set()
    for path in paths:
        if path.exists():
            found |= set(IMPLEMENTED.findall(path.read_text(encoding="utf-8")))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", type=Path, default=DEFAULT_DOC)
    ap.add_argument("--checker", type=Path, action="append", default=None)
    args = ap.parse_args()

    checkers = args.checker or DEFAULT_CHECKERS
    claims = claimed_status(args.rules)
    implemented = implemented_ids(checkers)

    overclaims = sorted(r for r, s in claims.items()
                        if AUTOMATIC in s and r not in implemented)
    unlisted = sorted(r for r in implemented if r not in claims)

    print(f"rule index: {args.rules.relative_to(REPO)}")
    print(f"  {len(claims)} rules listed, {len(implemented)} implemented by "
          f"{len(checkers)} checker(s)")
    if unlisted:
        print(f"  implemented but absent from the index: {' '.join(unlisted)}")
    if overclaims:
        print(f"OVERCLAIM: marked automatic with no implementation: "
              f"{' '.join(overclaims)}")
        return 1
    print("  no coverage overclaims")
    return 0


if __name__ == "__main__":
    sys.exit(main())
