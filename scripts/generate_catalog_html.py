#!/usr/bin/env python3
"""Generate a static, read-only HTML catalog page from registry/index.json.

Usage: generate_catalog_html.py

This is the "Web portal" from .trellis/spec/architecture/04-audience-distribution-channels.md
Phase 1 form: no server, no DB, no auth - just a static page rendered from the same
index generate_index.py already produces. It only shows *published* (approved)
skills and their install commands - actual submission/upload always goes through
review_pipeline.py (a raw upload widget here would bypass the review gate, which
defeats the point - see .trellis/spec/security/05-solo-operator-playbook.md).
For the pipeline/audit trail itself, see generate_audit_html.py -> audit.html.

Visual style: see scripts/_style.py.
"""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CSS, topbar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "registry" / "index.json"
OUT = ROOT / "registry" / "catalog.html"

RISK_COLOR = {"low": "var(--green)", "medium": "var(--amber)", "high": "var(--red)", "unknown": "var(--muted)"}
SOURCE_LABEL = {
    "collected-external": "外部采集",
    "colleague-submitted": "同事投稿",
    "self-authored": "自己编写",
}

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>SKILL-HUB — Catalog</title>
<style>
{css}
  .grid {{ display: grid; grid-template-columns: 1fr; gap: 18px; }}
  .card {{
    border: 2px solid var(--border); background: #fff; padding: 20px 24px;
    box-shadow: 4px 4px 0 var(--border); transition: transform .08s ease, box-shadow .08s ease;
  }}
  .card:hover {{ transform: translate(-2px,-2px); box-shadow: 6px 6px 0 var(--border); }}
  .card h2 {{ margin: 0 0 10px 0; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .badge {{
    display: inline-block; font-size: 0.68rem; padding: 3px 10px; font-weight: 700;
    border: 2px solid var(--border); background: #fff; color: var(--ink); text-transform: uppercase;
  }}
  .badge.risk {{ color: white; border-color: transparent; }}
  .desc {{ color: #3a3630; margin: 10px 0 16px; line-height: 1.55; font-size: 0.92rem; }}
  .install-label {{ font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; font-weight: 700; }}
  .install {{
    background: var(--bg); border: 2px solid var(--border); padding: 12px 14px;
    font-family: ui-monospace, "SF Mono", monospace; font-size: 0.8rem; overflow-x: auto;
    white-space: pre; line-height: 1.6;
  }}
</style>
</head>
<body>
{topbar}
<h1>SKILL 目录</h1>
<p class="meta">内网 skill 目录 — 只展示 <code>approved</code> 状态的 skill；安装口令随点随拿，不需要登录。发布/上传走 <code>review_pipeline.py</code>，不走网页，这里是浏览 + 下载专用页。</p>
<div class="stats">
  <div class="stat"><div class="n">{approved_count}</div><div class="label">Skills Approved</div></div>
  <div class="stat"><div class="n">{low_risk_count}</div><div class="label">Low Risk</div></div>
</div>
<input id="search" type="text" placeholder="搜索 skill 名称或描述…" oninput="filterCards(this.value)">
<div class="grid" id="grid">
{skills_html}
</div>
<script>
function filterCards(q) {{
  q = q.toLowerCase();
  document.querySelectorAll('.card').forEach(c => {{
    c.style.display = c.dataset.search.includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>
"""

SKILL_TEMPLATE = """<div class="card" data-search="{search_key}">
  <h2>{name}
    <span class="badge risk" style="background:{risk_color}">风险: {risk_tier}</span>
    <span class="badge">{source_label}</span>
  </h2>
  <p class="desc">{description}</p>
  <div class="install-label">OpenCode / 任何读 agentskills.io 目录的工具</div>
  <div class="install">bash scripts/install.sh {name} ~/.config/opencode/skills</div>
  <div class="install-label" style="margin-top:10px">Claude Code</div>
  <div class="install">/plugin marketplace add https://skill-hub.internal/.claude-plugin/marketplace.json
/plugin install {name}@skill-hub</div>
</div>
"""


def main():
    if not INDEX.exists():
        print(f"error: {INDEX} not found - run generate_index.py first", file=sys.stderr)
        raise SystemExit(1)

    data = json.loads(INDEX.read_text())
    skills = data.get("skills", [])
    low_risk_count = sum(1 for s in skills if s.get("risk_tier") == "low")

    if not skills:
        skills_html = '<p class="empty">暂无 approved 的 skill。</p>'
    else:
        blocks = []
        for s in skills:
            blocks.append(SKILL_TEMPLATE.format(
                name=html.escape(s["name"]),
                description=html.escape(s["description"]),
                source_label=html.escape(SOURCE_LABEL.get(s["source"], s["source"])),
                risk_tier=html.escape(s["risk_tier"]),
                risk_color=RISK_COLOR.get(s["risk_tier"], RISK_COLOR["unknown"]),
                search_key=html.escape((s["name"] + " " + s["description"]).lower()),
            ))
        skills_html = "\n".join(blocks)

    OUT.write_text(PAGE_TEMPLATE.format(
        css=CSS, topbar=topbar("catalog"), skills_html=skills_html,
        approved_count=len(skills), low_risk_count=low_risk_count,
    ))
    print(f"wrote {OUT} ({len(skills)} skills)")


if __name__ == "__main__":
    main()
