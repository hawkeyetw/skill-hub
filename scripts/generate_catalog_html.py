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
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "registry" / "index.json"
OUT = ROOT / "registry" / "catalog.html"

RISK_COLOR = {"low": "#2e7d32", "medium": "#e65100", "high": "#c62828", "unknown": "#616161"}
SOURCE_LABEL = {
    "collected-external": "外部采集",
    "colleague-submitted": "同事投稿",
    "self-authored": "自己编写",
}

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>skill-hub</title>
<style>
  :root {{ --border: #e3e3e3; --bg-soft: #f7f7f8; --accent: #111; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; max-width: 920px; margin: 0 auto; padding: 32px 20px 80px; color: #1a1a1a; background: #fff; }}
  nav {{ display: flex; gap: 18px; margin-bottom: 28px; font-size: 0.9rem; }}
  nav a {{ color: #555; text-decoration: none; padding: 4px 0; border-bottom: 2px solid transparent; }}
  nav a.active {{ color: #111; border-color: #111; font-weight: 600; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 6px; letter-spacing: -0.01em; }}
  .meta {{ color: #666; font-size: 0.85rem; margin-bottom: 20px; }}
  #search {{ width: 100%; padding: 10px 14px; font-size: 0.95rem; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 22px; }}
  #search:focus {{ outline: none; border-color: #999; }}
  .grid {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
  .card {{ border: 1px solid var(--border); border-radius: 12px; padding: 18px 22px; transition: box-shadow .15s ease; }}
  .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
  .card h2 {{ margin: 0 0 8px 0; font-size: 1.15rem; display: flex; align-items: center; gap: 10px; }}
  .badge {{ display: inline-block; font-size: 0.7rem; padding: 3px 9px; border-radius: 10px; color: white; font-weight: 500; }}
  .desc {{ color: #333; margin: 10px 0 14px; line-height: 1.5; font-size: 0.92rem; }}
  .install-label {{ font-size: 0.72rem; color: #888; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }}
  .install {{ background: var(--bg-soft); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; font-family: ui-monospace, "SF Mono", monospace; font-size: 0.8rem; overflow-x: auto; white-space: pre; line-height: 1.6; }}
  .empty {{ color: #999; font-style: italic; text-align: center; padding: 40px 0; }}
</style>
</head>
<body>
<nav>
  <a href="catalog.html" class="active">Catalog（可安装的 skill）</a>
  <a href="audit.html">Review Pipeline（审查记录）</a>
</nav>
<h1>skill-hub</h1>
<p class="meta">内网 skill 目录 — 只展示 <code>approved</code> 状态的 skill；安装口令随点随拿，不需要登录。发布/上传走 <code>review_pipeline.py</code>，不走网页——这里是浏览+下载专用页。</p>
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
    <span class="badge" style="background:{risk_color}">风险: {risk_tier}</span>
    <span class="badge" style="background:#455a64">{source_label}</span>
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

    OUT.write_text(PAGE_TEMPLATE.format(skills_html=skills_html))
    print(f"wrote {OUT} ({len(skills)} skills)")


if __name__ == "__main__":
    main()
