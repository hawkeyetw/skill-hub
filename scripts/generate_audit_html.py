#!/usr/bin/env python3
"""Render registry/audit-log.jsonl (written by review_pipeline.py) as a static HTML
timeline of every review run - this is the "how do I see the pipeline itself, not
just the end result" view. No git-log spelunking required.

Usage: generate_audit_html.py
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "registry" / "audit-log.jsonl"
OUT = ROOT / "registry" / "audit.html"

OUTCOME_STYLE = {
    "approved": ("#2e7d32", "已发布"),
    "rejected": ("#c62828", "已拒绝"),
    "pending_manual_approval": ("#e65100", "等待人工确认"),
}

PAGE_HEAD = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>skill-hub — review pipeline</title>
<style>
  :root { --border: #e3e3e3; --bg-soft: #f7f7f8; }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, "Segoe UI", sans-serif; max-width: 920px; margin: 0 auto; padding: 32px 20px 80px; color: #1a1a1a; background: #fff; }
  nav { display: flex; gap: 18px; margin-bottom: 28px; font-size: 0.9rem; }
  nav a { color: #555; text-decoration: none; padding: 4px 0; border-bottom: 2px solid transparent; }
  nav a.active { color: #111; border-color: #111; font-weight: 600; }
  h1 { font-size: 1.5rem; margin: 0 0 6px; }
  .meta { color: #666; font-size: 0.85rem; margin-bottom: 28px; }
  .run { border: 1px solid var(--border); border-radius: 10px; margin-bottom: 14px; overflow: hidden; }
  .run-head { display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: var(--bg-soft); flex-wrap: wrap; }
  .run-head .name { font-weight: 600; font-size: 1rem; }
  .pill { font-size: 0.72rem; padding: 2px 9px; border-radius: 10px; color: white; }
  .ts { margin-left: auto; color: #888; font-size: 0.78rem; font-family: ui-monospace, monospace; }
  .run-body { padding: 12px 16px; font-size: 0.85rem; }
  .finding { font-family: ui-monospace, monospace; font-size: 0.78rem; background: #fff5f5; border-left: 3px solid #c62828; padding: 4px 10px; margin: 4px 0; border-radius: 3px; }
  .stage { margin-top: 8px; }
  .stage-label { font-weight: 600; color: #444; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.03em; }
  .empty { color: #999; font-style: italic; }
</style>
</head>
<body>
<nav>
  <a href="catalog.html">Catalog（可安装的 skill）</a>
  <a href="audit.html" class="active">Review Pipeline（审查记录）</a>
</nav>
<h1>Review Pipeline</h1>
<p class="meta">每一次 <code>review_pipeline.py</code> 运行的完整记录 — 静态扫描结果、是否需要沙箱、最终结论，全部持久化在 <code>registry/audit-log.jsonl</code>，不用翻 git log。</p>
"""

PAGE_TAIL = "</body>\n</html>\n"

RUN_TEMPLATE = """<div class="run">
  <div class="run-head">
    <span class="name">{name}</span>
    <span class="pill" style="background:#455a64">Track {track}</span>
    <span class="pill" style="background:#00695c">{source}</span>
    <span class="pill" style="background:{outcome_color}">{outcome_label}</span>
    <span class="ts">{timestamp}</span>
  </div>
  <div class="run-body">
    {body}
  </div>
</div>
"""


def render_findings(findings):
    if not findings:
        return '<div class="finding" style="background:#f1f8f1;border-color:#2e7d32;color:#2e7d32">no findings</div>'
    return "".join(
        f'<div class="finding">[{html.escape(f.get("category",""))}] {html.escape(f.get("rule",""))} — {html.escape(f.get("file","").split("/")[-1])}</div>'
        for f in findings
    )


def render_run(rec: dict) -> str:
    outcome = rec.get("outcome", "unknown")
    color, label = OUTCOME_STYLE.get(outcome, ("#616161", outcome))

    body_parts = []
    static = rec.get("static_scan")
    if static:
        body_parts.append(f'<div class="stage"><div class="stage-label">Static scan ({html.escape(static.get("secret_scanner","?"))}) — {html.escape(static.get("verdict","?"))}</div>{render_findings(static.get("findings"))}</div>')

    if rec.get("sandbox_required"):
        sandbox = rec.get("sandbox_check")
        if sandbox:
            detail = sandbox.get("detail", sandbox.get("verdict", ""))
            body_parts.append(f'<div class="stage"><div class="stage-label">Sandbox — {html.escape(sandbox.get("verdict","?"))}</div><div class="finding" style="background:#f5f5f5;border-color:#888;color:#333">{html.escape(str(detail))}</div></div>')
        else:
            body_parts.append('<div class="stage"><div class="stage-label">Sandbox</div><div class="finding" style="background:#f5f5f5;border-color:#888;color:#333">required but not reached (rejected earlier)</div></div>')
    else:
        body_parts.append('<div class="stage"><div class="stage-label">Sandbox</div><div class="finding" style="background:#f5f5f5;border-color:#888;color:#333">skipped (Track I, low risk)</div></div>')

    if outcome == "rejected":
        body_parts.append(f'<div class="stage"><div class="stage-label">Rejection reason</div><div class="finding">{html.escape(rec.get("rejection_reason",""))}</div></div>')

    return RUN_TEMPLATE.format(
        name=html.escape(rec.get("skill", "?")),
        track=html.escape(rec.get("track", "?")),
        source=html.escape(rec.get("source", "?")),
        outcome_color=color,
        outcome_label=html.escape(label),
        timestamp=html.escape(rec.get("timestamp", "")),
        body="".join(body_parts),
    )


def main():
    if not LOG.exists():
        records = []
    else:
        records = [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]

    records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

    if not records:
        body = '<p class="empty">还没有跑过任何审查记录。</p>'
    else:
        body = "\n".join(render_run(r) for r in records)

    OUT.write_text(PAGE_HEAD + body + PAGE_TAIL)
    print(f"wrote {OUT} ({len(records)} runs)")


if __name__ == "__main__":
    main()
