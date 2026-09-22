"""Run the PCBA study with FreeCAD's bundled Python and isolated output files."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


PROJECT = Path(__file__).resolve().parents[1]
RUNTIME = Path("/Applications/FreeCAD.app/Contents/Resources")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("generate", "check", "preview"))
    parser.add_argument("model", nargs="?", type=Path)
    parser.add_argument("--variant", choices=("baseline", "e6-302030", "e6-bottom-usb", "e6-84x52", "e6-83x51", "e6-84x52-detail"), default="baseline",
                        help="Generation layout; saved models carry their own parameters.")
    parser.add_argument("--output-dir", type=Path, help="A new directory; existing paths are refused.")
    args = parser.parse_args()
    if args.action != "generate" and args.model is None:
        parser.error("check and preview require a saved .FCStd model")
    if args.action == "generate" and args.model is not None:
        parser.error("generate uses enclosure/pcba-layout.FCMacro, not an input model")
    if args.action != "generate" and args.variant != "baseline":
        parser.error("--variant applies only to generate")
    executable = RUNTIME / "bin" / ("freecad" if args.action == "preview" else "freecadcmd")
    if not executable.is_file():
        parser.error(f"FreeCAD runtime not found: {executable}")

    source_name = {"baseline": "pcba-layout.FCStd", "e6-302030": "pcba-e6-302030.FCStd",
                   "e6-bottom-usb": "pcba-e6-bottom-usb.FCStd", "e6-84x52": "pcba-e6-84x52.FCStd",
                   "e6-83x51": "pcba-e6-83x51.FCStd", "e6-84x52-detail": "pcba-e6-84x52-detail.FCStd"}[args.variant]
    source = (args.model or PROJECT / "enclosure" / source_name).resolve()
    if args.action != "generate" and not source.is_file():
        parser.error(f"Saved model not found: {source}")
    source_bytes = source.read_bytes() if source.exists() else None
    before_hash = hashlib.sha256(source_bytes).hexdigest() if source_bytes is not None else None
    if args.output_dir:
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=False)
    else:
        runs = PROJECT / "artifacts/freecad"
        runs.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix=args.action + "-", dir=runs))

    git = subprocess.run(["git", "status", "--porcelain", "--", str(source)],
                         cwd=PROJECT, text=True, capture_output=True, check=True)
    processes = subprocess.run(["pgrep", "-fl", str(RUNTIME / "bin/freecad")],
                               text=True, capture_output=True, check=False)
    audit = {"saved_source": str(source), "source_sha256_before": before_hash,
             "git_status": git.stdout.strip(), "freecad_processes": processes.stdout.strip(),
             "unsaved_gui_edits": "Not observable across processes; never overwrite the source.",
             "action": args.action, "output": str(output)}
    job = {"action": args.action, "output": str(output), "project": str(PROJECT),
           "variant": args.variant}
    if args.action != "generate":
        snapshot = output / "input.FCStd"
        snapshot.write_bytes(source_bytes)
        job["model"] = str(snapshot)
    (output / "job.json").write_text(json.dumps(job, indent=2) + "\n")
    audit_path = output / "source-audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n")
    print(f"Output: {output}", flush=True)
    print("Existing model preserved. Unsaved edits in other FreeCAD processes are not read.", flush=True)

    env = os.environ.copy()
    env.update(PYTHONHOME=str(RUNTIME), PYTHONPATH=str(RUNTIME / "lib"),
               NFC_CARD_FREECAD_JOB=str(output / "job.json"))
    worker = Path(__file__).with_name("freecad-worker.py")
    entry = worker
    if args.action == "preview":
        entry = output / "preview.FCMacro"
        entry.write_text("import FreeCAD as App\nimport FreeCADGui as Gui\nimport runpy\n"
                         f"runpy.run_path({str(worker)!r}, run_name='__main__')\n")
    command = [str(executable), "--user-cfg", str(output / "user.cfg"),
               "--system-cfg", str(output / "system.cfg"), str(entry)]
    failure = None
    try:
        with (output / "freecad.log").open("w") as log:
            completed = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                       timeout=90, check=False)
        if completed.returncode:
            failure = f"FreeCAD exited with {completed.returncode}"
    except subprocess.TimeoutExpired:
        failure = "FreeCAD timed out; its isolated process was stopped"
    finally:
        after_hash = hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else None
        audit["source_sha256_after"] = after_hash
        audit["source_unchanged"] = before_hash == after_hash
        audit_path.write_text(json.dumps(audit, indent=2) + "\n")
    result_path = output / "result.json"
    result = json.loads(result_path.read_text()) if result_path.exists() else {"ok": False, "error": "No completion marker"}
    if failure or not result.get("ok") or not audit["source_unchanged"]:
        print(json.dumps({"process_error": failure, "result": result,
                          "source_unchanged": audit["source_unchanged"],
                          "log": str(output / "freecad.log")}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
