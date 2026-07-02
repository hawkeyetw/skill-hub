#!/usr/bin/env python3
"""skill-hub static review scanner (Track E/I stage 2, see .trellis/spec/security/02-lifecycle-controls.md).

Usage: static_scan.py <skill-dir>

Reads <skill-dir>/skill-hub.json for the declared `source`, then scans every text
file in the skill for secrets / dangerous shell patterns / prompt-injection markers /
anomalous file padding. Prints a JSON report to stdout and exits non-zero on REJECT.

Deliberately does NOT trust the manifest's `risk_tier` for pass/fail decisions -
that field is self-declared by the skill and, for externally-sourced skills, must be
treated as untrusted input (see architecture/01-registry-model.md decision 3).
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# TruffleHog (trufflesecurity/trufflehog) is the market-standard secret scanner -
# see .trellis/spec/security research: it validates secret *structure* (and, where
# possible, live-verifies against the provider) instead of naive substring/regex
# matching, which is why it doesn't false-positive on placeholder strings the way
# a hand-rolled regex does. Used here if the binary is on PATH; the regex list
# below is kept ONLY as a backstop for environments where it isn't installed.
TRUFFLEHOG_BIN = shutil.which("trufflehog")

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "aws_access_key_id"),
    (r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{30,}", "aws_secret_key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private_key_block"),
    (r"(?i)(api[_-]?key|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]", "generic_api_key"),
]

DANGEROUS_SHELL_PATTERNS = [
    (r"curl[^\n]*\|\s*(sudo\s+)?(ba)?sh", "curl_pipe_shell"),
    (r"wget[^\n]*\|\s*(sudo\s+)?(ba)?sh", "wget_pipe_shell"),
    (r"\brm\s+-rf\s+[/~]", "rm_rf_root_or_home"),
    (r"base64\s+-d[^\n]*\|\s*(ba)?sh", "base64_decode_pipe_shell"),
    (r"\beval\s*\(", "eval_call"),
]

PROMPT_INJECTION_PATTERNS = [
    (r"(?i)ignore (all )?previous instructions", "ignore_previous_instructions"),
    (r"(?i)don'?t tell the user", "dont_tell_user"),
    (r"(?i)do not (mention|tell|inform) the user", "dont_inform_user"),
    (r"[​-‏‪-‮﻿]", "zero_width_or_bidi_char"),
    (r"(?i)\.ssh/id_rsa|\.env\b.*exfiltrat|for [\"']?debugging[\"']? purposes", "credential_read_social_engineering"),
]

# HTML/markdown comments are common and benign on their own (code examples, doc
# asides) - only flag one if its CONTENT looks instructional/suspicious, not just
# because a comment exists. (First pass flagged every HTML comment including
# legitimate ones in example code - see .trellis/spec/security/02-lifecycle-controls.md
# for why content-based detection beats presence-based detection here.)
SUSPICIOUS_COMMENT_CONTENT = re.compile(
    r"(?i)(ignore|disregard|override).{0,30}(instruction|rule|safety)"
    r"|system\s*:|assistant\s*:|do not (tell|mention|inform)"
    r"|read .{0,40}(ssh|\.env|credential|secret|token)",
    re.DOTALL,
)

# Files this small in visible content but this large on disk are suspicious
# (ref: JFrog's "omnicogg" ClawHub dropper - payload hidden in a padded README).
SIZE_ANOMALY_BYTES = 200_000
SIZE_ANOMALY_RATIO = 20  # file_size / stripped_content_size


def load_manifest(skill_dir: Path):
    manifest_path = skill_dir / "skill-hub.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text())


def track_for(manifest: dict | None) -> str:
    if manifest is None:
        return "E"  # no manifest = treat as external/untrusted by default
    source = manifest.get("source", "collected-external")
    return "I" if source in ("colleague-submitted", "self-authored") else "E"


def run_trufflehog(skill_dir: Path, findings: list):
    """Real secret-detection layer. Falls back silently to the regex list in
    scan_file() if the binary isn't installed - see TRUFFLEHOG_BIN above."""
    if TRUFFLEHOG_BIN is None:
        return
    result = subprocess.run(
        [TRUFFLEHOG_BIN, "filesystem", str(skill_dir), "--no-update", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{") or '"DetectorName"' not in line:
            continue
        try:
            hit = json.loads(line)
        except json.JSONDecodeError:
            continue
        verified = hit.get("Verified", False)
        findings.append({
            "severity": "high",
            "category": "secret",
            "rule": f"trufflehog_{hit.get('DetectorName', 'unknown')}" + ("_verified_live" if verified else "_unverified"),
            "file": hit.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {}).get("file", str(skill_dir)),
        })


def scan_file(path: Path, findings: list):
    try:
        raw = path.read_bytes()
    except OSError:
        return
    text = raw.decode("utf-8", errors="ignore")

    if TRUFFLEHOG_BIN is None:  # backstop only - see run_trufflehog()
        for pattern, label in SECRET_PATTERNS:
            if re.search(pattern, text):
                findings.append({"severity": "high", "category": "secret", "rule": f"regex_backstop_{label}", "file": str(path)})

    for pattern, label in DANGEROUS_SHELL_PATTERNS:
        if re.search(pattern, text):
            findings.append({"severity": "high", "category": "dangerous_shell", "rule": label, "file": str(path)})

    for pattern, label in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.DOTALL):
            findings.append({"severity": "high", "category": "prompt_injection", "rule": label, "file": str(path)})

    for comment in re.findall(r"<!--(.*?)-->", text, re.DOTALL):
        if SUSPICIOUS_COMMENT_CONTENT.search(comment):
            findings.append({"severity": "high", "category": "prompt_injection", "rule": "suspicious_hidden_comment",
                              "file": str(path), "detail": comment.strip()[:120]})

    stripped_len = len(text.strip())
    if len(raw) > SIZE_ANOMALY_BYTES and stripped_len > 0 and len(raw) / max(stripped_len, 1) > SIZE_ANOMALY_RATIO:
        findings.append({"severity": "high", "category": "padded_file", "rule": "size_anomaly", "file": str(path),
                          "detail": f"{len(raw)} bytes on disk vs ~{stripped_len} bytes of visible content"})


def validate_frontmatter(skill_dir: Path, findings: list):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        findings.append({"severity": "high", "category": "structure", "rule": "missing_skill_md", "file": str(skill_dir)})
        return
    text = skill_md.read_text(errors="ignore")
    if not text.startswith("---"):
        findings.append({"severity": "medium", "category": "structure", "rule": "missing_frontmatter", "file": str(skill_md)})
        return
    fm_end = text.find("---", 3)
    frontmatter = text[3:fm_end] if fm_end > 0 else ""
    for required in ("name:", "description:"):
        if required not in frontmatter:
            findings.append({"severity": "medium", "category": "structure", "rule": f"missing_field_{required.rstrip(':')}", "file": str(skill_md)})


def main():
    if len(sys.argv) != 2:
        print("usage: static_scan.py <skill-dir>", file=sys.stderr)
        sys.exit(2)

    skill_dir = Path(sys.argv[1]).resolve()
    manifest = load_manifest(skill_dir)
    track = track_for(manifest)

    findings: list = []
    validate_frontmatter(skill_dir, findings)
    run_trufflehog(skill_dir, findings)  # whole-directory scan, not per-file
    for path in sorted(skill_dir.rglob("*")):
        if path.is_file() and path.name != "skill-hub.json":
            scan_file(path, findings)

    high_severity = [f for f in findings if f["severity"] == "high"]
    verdict = "REJECT" if high_severity else "PASS"

    report = {
        "skill": skill_dir.name,
        "track": track,
        "source": (manifest or {}).get("source", "unknown"),
        "declared_risk_tier": (manifest or {}).get("risk_tier", "unknown"),
        "secret_scanner": "trufflehog" if TRUFFLEHOG_BIN else "regex_backstop (trufflehog not installed)",
        "verdict": verdict,
        "findings": findings,
    }
    print(json.dumps(report, indent=2))
    sys.exit(1 if verdict == "REJECT" else 0)


if __name__ == "__main__":
    main()
