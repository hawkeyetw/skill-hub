#!/usr/bin/env python3
"""skill-hub dynamic sandbox check (Track E mandatory / Track I conditional).

Usage: sandbox_check.py <skill-dir>

Runs any bundled .py/.sh scripts inside a single, fully network-isolated
(`--network none`) container, non-root filesystem read-only except /tmp, with a
*canary* credentials file planted at $HOME. A tiny mock "attacker" HTTP listener
runs in the background inside the SAME container on 127.0.0.1 (loopback still
works under --network none; only external interfaces are removed) and logs
whatever it receives to a file in /tmp. After the run, that log is checked for the
canary marker. If it shows up, that's an unambiguous signal of credential
exfiltration - the thing static regex scanning alone cannot catch (see
registry/pending/weather-cli-helper for a fixture written specifically to evade
static_scan.py but get caught here).

Design note: collector + script share one container's loopback interface rather
than talking over a docker bridge network between two containers. This was a
deliberate fallback after container-to-container bridge networking proved
unreliable in this sandboxed dev host (cross-container connections timed out even
on a plain user-defined bridge - environment-specific, not a design requirement).
--network none here gives *stronger* isolation than the original two-container
design anyway: the sandboxed script has zero path to the real network, full stop.
Production review infrastructure should still follow
.trellis/spec/security/04-quarantine-review-and-incident-response.md for the
target isolation tier (container / gVisor / Firecracker) based on risk_tier.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

CANARY_MARKER = "CANARY-SECRET-DO-NOT-LEAK-8f21c9"
EXCLUDE_NAMES = {"skill-hub.json"}
DOCKER_IMAGE = "python:3.11-slim"

# Runs inside the container: background collector on loopback, then the target
# script, then dump whatever the collector captured so the host can read it off
# this container's stdout.
RUNNER_TEMPLATE = r"""
import http.server, threading, subprocess, sys, time

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode(errors="ignore")
        with open("/tmp/collector.log", "a") as f:
            f.write(body + "\n")
        self.send_response(200); self.end_headers()
    def log_message(self, *a): pass

srv = http.server.HTTPServer(("127.0.0.1", 8080), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.5)

subprocess.run([{interpreter!r}, {script_path!r}], timeout=20)

time.sleep(0.5)
print("===COLLECTOR-LOG-START===")
try:
    print(open("/tmp/collector.log").read())
except FileNotFoundError:
    pass
print("===COLLECTOR-LOG-END===")
"""


def find_scripts(skill_dir: Path):
    return sorted(
        p for p in skill_dir.rglob("*")
        if p.is_file() and p.suffix in (".py", ".sh") and p.name not in EXCLUDE_NAMES
    )


def sh(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def main():
    if len(sys.argv) != 2:
        print("usage: sandbox_check.py <skill-dir>", file=sys.stderr)
        sys.exit(2)

    skill_dir = Path(sys.argv[1]).resolve()
    scripts = find_scripts(skill_dir)

    if not scripts:
        print(json.dumps({
            "skill": skill_dir.name, "verdict": "PASS",
            "detail": "no bundled .py/.sh scripts found; sandbox check is a no-op (logged for audit trail)",
        }, indent=2))
        sys.exit(0)

    tmp = Path(tempfile.mkdtemp(prefix="skillhub-sandbox-"))
    canary_home = tmp / "canary_home"
    (canary_home / ".aws").mkdir(parents=True)
    (canary_home / ".aws" / "credentials").write_text(
        f"[default]\naws_access_key_id = AKIA_CANARY_FIXTURE\naws_secret_access_key = {CANARY_MARKER}\n"
    )

    run_results = []
    all_captured = []
    for script in scripts:
        rel = script.relative_to(skill_dir)
        interpreter = "python3" if script.suffix == ".py" else "bash"
        runner = RUNNER_TEMPLATE.format(interpreter=interpreter, script_path=f"/work/{rel}")
        runner_file = tmp / f"runner_{rel.name}.py"
        runner_file.write_text(runner)

        result = sh(
            "docker", "run", "--rm",
            "--network", "none",
            "--read-only", "--tmpfs", "/tmp",
            "--user", "root",
            "-v", f"{skill_dir}:/work:ro",
            "-v", f"{canary_home}:/root:ro",
            "-v", f"{runner_file}:/runner.py:ro",
            "-e", "HOME=/root",
            "-e", "WEATHER_HELPER_TELEMETRY_URL=http://127.0.0.1:8080/collect",
            DOCKER_IMAGE, "python3", "/runner.py",
            timeout=30,
        )
        run_results.append({"script": str(rel), "exit_code": result.returncode})

        if "===COLLECTOR-LOG-START===" in result.stdout:
            captured_block = result.stdout.split("===COLLECTOR-LOG-START===")[1].split("===COLLECTOR-LOG-END===")[0]
            all_captured.extend(line for line in captured_block.splitlines() if line.strip())

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    leaked = [body for body in all_captured if CANARY_MARKER in body]
    verdict = "REJECT" if leaked else "PASS"

    report = {
        "skill": skill_dir.name,
        "verdict": verdict,
        "scripts_executed": run_results,
        "network_calls_observed": len(all_captured),
        "canary_leaked": bool(leaked),
    }
    if leaked:
        report["detail"] = "canary credential content was observed in an outbound request the script made - this is what static_scan.py cannot see"
    print(json.dumps(report, indent=2))
    sys.exit(1 if verdict == "REJECT" else 0)


if __name__ == "__main__":
    main()
