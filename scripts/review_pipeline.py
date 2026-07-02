#!/usr/bin/env python3
"""skill-hub review pipeline orchestrator.

Usage:
  review_pipeline.py <skill-name>            # run automated checks, stop before publish
  review_pipeline.py <skill-name> --approve  # run automated checks, then publish if clean

Implements the Track E / Track I branching from
.trellis/spec/security/02-lifecycle-controls.md and the six-step flow from
.trellis/spec/security/05-solo-operator-playbook.md:

  1. intake (already done - skill sits in registry/pending/<name>/)
  2. static scan (always, both tracks)
  3. human read-through of rendered SKILL.md (Track E: mandatory / Track I: conditional)
     -> this script can't actually read for you; it prints the rendered content and
        requires --approve as your explicit sign-off that you did
  4. sandbox (Track E: mandatory / Track I: conditional on risk_tier/declared capabilities)
  5. your decision (--approve moves it to approved/, otherwise it stays pending)
  6. ongoing maintenance is out of scope for this script

Every run appends one record to registry/audit-log.jsonl regardless of outcome -
this is what generate_audit_html.py renders as the "review pipeline" view, so you
don't have to reconstruct history from git log. See
.trellis/spec/security/02-lifecycle-controls.md step 8 (Monitoring & Audit).
"""
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PENDING = ROOT / "registry" / "pending"
APPROVED = ROOT / "registry" / "approved"
REJECTED = ROOT / "registry" / "rejected"
AUDIT_LOG = ROOT / "registry" / "audit-log.jsonl"


def track_for(manifest: dict | None) -> str:
    if manifest is None:
        return "E"
    return "I" if manifest.get("source") in ("colleague-submitted", "self-authored") else "E"


def needs_sandbox(track: str, manifest: dict) -> bool:
    if track == "E":
        return True  # always, regardless of declared risk_tier - self-declared, untrusted
    risk_tier = manifest.get("risk_tier", "medium")
    return (
        risk_tier != "low"
        or manifest.get("requires_shell", False)
        or bool(manifest.get("declared_network_domains"))
    )


def run(cmd: list[str]) -> tuple[int, dict | None, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return result.returncode, json.loads(result.stdout), result.stdout
    except json.JSONDecodeError:
        return result.returncode, None, result.stdout + result.stderr


def append_audit(record: dict):
    record["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")


def reject(skill_dir: Path, reason: str, detail, audit: dict):
    dest = REJECTED / skill_dir.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(skill_dir), dest)
    (dest / "REJECTION_REASON.json").write_text(json.dumps({"reason": reason, "detail": detail}, indent=2))
    print(f"\n>>> REJECTED: {skill_dir.name} — {reason}")
    print(f">>> moved to {dest}")
    audit["outcome"] = "rejected"
    audit["rejection_reason"] = reason
    audit["rejection_detail"] = detail
    append_audit(audit)


def main():
    if len(sys.argv) < 2:
        print("usage: review_pipeline.py <skill-name> [--approve]", file=sys.stderr)
        sys.exit(2)

    name = sys.argv[1]
    approve = "--approve" in sys.argv[2:]
    skill_dir = PENDING / name

    if not skill_dir.exists():
        print(f"no such pending skill: {skill_dir}", file=sys.stderr)
        sys.exit(2)

    manifest_path = skill_dir / "skill-hub.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    track = track_for(manifest)
    print(f"=== {name} — Track {track} ({(manifest or {}).get('source', 'unknown')}) ===\n")

    audit = {
        "skill": name,
        "track": track,
        "source": (manifest or {}).get("source", "unknown"),
        "declared_risk_tier": (manifest or {}).get("risk_tier", "unknown"),
    }

    print("--- Step 2: static scan ---")
    code, report, raw = run([sys.executable, str(ROOT / "scripts" / "static_scan.py"), str(skill_dir)])
    print(raw)
    audit["static_scan"] = report or {"raw": raw}
    if code != 0:
        reject(skill_dir, "static_scan_reject", report["findings"] if report else raw, audit)
        sys.exit(1)

    print("--- Step 3: human read-through ---")
    skill_md = skill_dir / "SKILL.md"
    mandatory_read = track == "E"
    print(f"track={track} -> read-through is {'MANDATORY' if mandatory_read else 'discretionary (static scan was clean)'}")
    print(f"rendered content of {skill_md.relative_to(ROOT)}:\n" + "-" * 60)
    print(skill_md.read_text())
    print("-" * 60)
    audit["read_through_required"] = mandatory_read

    sandbox_needed = needs_sandbox(track, manifest or {})
    audit["sandbox_required"] = sandbox_needed
    print(f"\n--- Step 4: sandbox — {'REQUIRED' if sandbox_needed else 'skipped (Track I, low risk, no shell/network declared)'} ---")
    if sandbox_needed:
        code, report, raw = run([sys.executable, str(ROOT / "scripts" / "sandbox_check.py"), str(skill_dir)])
        print(raw)
        audit["sandbox_check"] = report or {"raw": raw}
        if code != 0:
            reject(skill_dir, "sandbox_reject", report.get("detail") if report else raw, audit)
            sys.exit(1)

    print("\n--- Step 5: your decision ---")
    if not approve:
        print(f"All automated checks passed. Re-run with --approve once you've read the content above to publish {name}.")
        audit["outcome"] = "pending_manual_approval"
        append_audit(audit)
        sys.exit(0)

    dest = APPROVED / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(skill_dir), dest)
    if manifest is not None:
        manifest["review_status"] = "approved"
        (dest / "skill-hub.json").write_text(json.dumps(manifest, indent=2))
    print(f">>> APPROVED and published: {dest}")
    audit["outcome"] = "approved"
    append_audit(audit)


if __name__ == "__main__":
    main()
