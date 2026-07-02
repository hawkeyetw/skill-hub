#!/usr/bin/env python3
"""Generate the skill-hub index from registry/approved/.

Usage: generate_index.py

Writes:
  - registry/index.json               (portable, agentskills.io-flavored index)
  - registry/.claude-plugin/marketplace.json  (optional Claude Code compat export,
    same source data - see architecture/01-registry-model.md decision 1: Claude
    format is a secondary export, not the source of truth)

Mirrors Helm's `index.yaml` generation model: scan a directory of already-published
artifacts, emit a static index. No database involved (Phase 1 - see
architecture/03-deployment-and-auth.md).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPROVED = ROOT / "registry" / "approved"


def parse_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text()
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    fm: dict = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def build_index():
    entries = []
    for skill_dir in sorted(APPROVED.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        manifest_path = skill_dir / "skill-hub.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        fm = parse_frontmatter(skill_md)
        entries.append({
            "name": fm.get("name", skill_dir.name),
            "description": fm.get("description", ""),
            "source": manifest.get("source", "unknown"),
            "risk_tier": manifest.get("risk_tier", "unknown"),
            "review_status": manifest.get("review_status", "unknown"),
            "path": f"approved/{skill_dir.name}",
        })
    return entries


def write_agentskills_index(entries):
    out = ROOT / "registry" / "index.json"
    out.write_text(json.dumps({
        "generated_by": "skill-hub generate_index.py",
        "format": "agentskills.io-index-v0 (informal, see architecture/01-registry-model.md)",
        "skills": entries,
    }, indent=2))
    return out


def write_claude_marketplace(entries):
    out_dir = ROOT / "registry" / ".claude-plugin"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "marketplace.json"
    out.write_text(json.dumps({
        "name": "skill-hub",
        "owner": {"name": "cbw"},
        "metadata": {"description": "Internal curated skill registry (secondary Claude Code export)"},
        "plugins": [
            {"name": e["name"], "description": e["description"], "source": f"../{e['path']}"}
            for e in entries
        ],
    }, indent=2))
    return out


def main():
    entries = build_index()
    idx_path = write_agentskills_index(entries)
    mp_path = write_claude_marketplace(entries)
    print(f"wrote {idx_path} ({len(entries)} approved skills)")
    print(f"wrote {mp_path} (Claude Code compat export)")
    for e in entries:
        print(f"  - {e['name']} [{e['source']}, risk={e['risk_tier']}]")


if __name__ == "__main__":
    main()
