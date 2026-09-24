#!/usr/bin/env python3
"""Make a review-only Gerber set with the known E16-E19 outline clutter removed.

This is a narrow export workaround, not a PCB design or manufacturing release.
It refuses any outline that differs from the audited two-path shape. Run the
normal manufacturing checker on its output before using it for further review.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import zipfile
from pathlib import Path


CHECKER = Path(__file__).with_name("check-e16-manufacture.py")
spec = importlib.util.spec_from_file_location("manufacture_check", CHECKER)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def is_full_rectangle(path: list[tuple[float, float]]) -> bool:
    xs, ys = zip(*path)
    return (path[0] == path[-1] and len(path) == 5
            and abs(min(xs)) < 0.01 and abs(max(xs) - 84) < 0.01
            and abs(min(ys)) < 0.01 and abs(max(ys) - 52) < 0.01)


def clean_outline(raw: bytes) -> bytes:
    text = raw.decode("utf-8")
    paths = checker.gerber_draw_paths(text)
    if len(paths) != 2 or paths[0][0] != paths[0][-1] or paths[1][0] == paths[1][-1]:
        raise ValueError("expected one closed outline and one open J1 guide")
    if not all(any(abs(x - px) < 0.001 and abs(y - py) < 0.001 for px, py in paths[0])
               for x, y in checker.OUTLINE_MUST_HAVE):
        raise ValueError("main outline differs from the audited board")
    marker = "G54D11*\n"
    if text.count(marker) != 1 or not text.rstrip().endswith("M02*"):
        raise ValueError("unexpected Gerber commands around the J1 guide")
    cleaned = text.split(marker, 1)[0].rstrip() + "\n\nM02*\n"
    if checker.gerber_draw_paths(cleaned) != [paths[0]]:
        raise ValueError("outline extraction changed the retained contour")
    return cleaned.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if source == output or output.exists():
        raise SystemExit("output must be a new directory")
    zip_source = source / "NFC-E16-gerber.zip"
    if not zip_source.is_file():
        raise SystemExit(f"missing {zip_source}")

    with zipfile.ZipFile(zip_source) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise SystemExit("duplicate zip members")
        outline = [n for n in names if n.endswith(".GKO")]
        mechanical = [n for n in names if n.endswith(".GME")]
        if len(outline) != 1 or len(mechanical) != 1:
            raise SystemExit("expected exactly one GKO and one GME")
        cleaned = clean_outline(archive.read(outline[0]))
        mechanical_paths = checker.gerber_draw_paths(archive.read(mechanical[0]).decode("utf-8"))
        if len(mechanical_paths) != 1 or not is_full_rectangle(mechanical_paths[0]):
            raise SystemExit("mechanical layer contains more than the known reference rectangle")

        output.mkdir(parents=True)
        with zipfile.ZipFile(output / zip_source.name, "w") as dest:
            for info in archive.infolist():
                if info.filename == mechanical[0]:
                    continue
                dest.writestr(info, cleaned if info.filename == outline[0] else archive.read(info))

    for name in ("NFC-E16-bom.xlsx", "NFC-E16-cpl.xlsx", "NFC-E16-board-pdf.pdf"):
        shutil.copy2(source / name, output / name)
    print(f"Review set: {output} (GKO retained; J1 guide and GME reference removed)")


if __name__ == "__main__":
    main()
