#!/usr/bin/env python3
"""Render registry/audit-log.jsonl (written by review_pipeline.py) as a static HTML
timeline of every review run - this is the "how do I see the pipeline itself, not
just the end result" view. No git-log spelunking required.

Usage: generate_audit_html.py

Visual style: see scripts/_style.py.
"""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CSS, topbar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "registry" / "audit-log.jsonl"
OUT = ROOT / "registry" / "audit.html"

OUTCOME_STYLE = {
    "approved": ("var(--green)", "已发布"),
    "rejected": ("var(--red)", "已拒绝"),
    "pending_manual_approval": ("var(--amber)", "等待人工确认"),
}

PAGE_HEAD = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>SKILL-HUB — Review Pipeline</title>
<style>
{css}
  .run {{
    border: 2px solid var(--border); background: #fff; margin-bottom: 16px;
    box-shadow: 4px 4px 0 var(--border);
  }}
  .run-head {{ display: flex; align-items: center; gap: 10px; padding: 12px 18px; border-bottom: 2px solid var(--border); background: var(--bg); flex-wrap: wrap; }}
  .run-head .name {{ font-weight: 800; font-size: 1.02rem; }}
  .pill {{ font-size: 0.68rem; padding: 3px 10px; font-weight: 700; border: 2px solid var(--border); background: #fff; text-transform: uppercase; }}
  .pill.outcome {{ color: white; border-color: transparent; }}
  .ts {{ margin-left: auto; color: var(--muted); font-size: 0.76rem; font-family: ui-monospace, monospace; }}
  .run-body {{ padding: 14px 18px; font-size: 0.85rem; }}
  .finding {{ font-family: ui-monospace, monospace; font-size: 0.78rem; background: #fff; border: 1.5px solid var(--red); color: var(--red); padding: 5px 10px; margin: 4px 0; }}
  .finding.ok {{ border-color: var(--green); color: var(--green); }}
  .finding.neutral {{ border-color: #ddd6c8; color: var(--muted); }}
  .stage {{ margin-top: 10px; }}
  .stage-label {{ font-weight: 700; color: var(--ink); font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }}
</style>
</head>
<body>
{topbar}
<h1>REVIEW PIPELINE</h1>
<p class="meta">每一次 <code>review_pipeline.py</code> 运行的完整记录 — 静态扫描结果、是否需要沙箱、最终结论，全部持久化在 <code>registry/audit-log.jsonl</code>，不用翻 git log。</p>
"""

PAGE_TAIL = "</body>\n</html>\n"

RUN_TEMPLATE = """<div class="run">
  <div class="run-head">
    <span class="name">{name}</span>
    <span class="pill">TRACK {track}</span>
    <span class="pill">{source}</span>
    <span class="pill outcome" style="background:{outcome_color}">{outcome_label}</span>
    <span class="ts">{timestamp}</span>
  </div>
  <div class="run-body">
    {body}
  </div>
</div>
"""


def render_findings(findings):
    if not findings:
        return '<div class="finding ok">no findings</div>'
    return "".join(
        f'<div class="finding">[{html.escape(f.get("category",""))}] {html.escape(f.get("rule",""))} — {html.escape(f.get("file","").split("/")[-1])}</div>'
        for f in findings
    )


def render_run(rec: dict) -> str:
    outcome = rec.get("outcome", "unknown")
    color, label = OUTCOME_STYLE.get(outcome, ("var(--muted)", outcome))

    body_parts = []
    static = rec.get("static_scan")
    if static:
        body_parts.append(f'<div class="stage"><div class="stage-label">Static scan ({html.escape(static.get("secret_scanner","?"))}) — {html.escape(static.get("verdict","?"))}</div>{render_findings(static.get("findings"))}</div>')

    if rec.get("sandbox_required"):
        sandbox = rec.get("sandbox_check")
        if sandbox:
            detail = sandbox.get("detail", sandbox.get("verdict", ""))
            body_parts.append(f'<div class="stage"><div class="stage-label">Sandbox — {html.escape(sandbox.get("verdict","?"))}</div><div class="finding neutral">{html.escape(str(detail))}</div></div>')
        else:
            body_parts.append('<div class="stage"><div class="stage-label">Sandbox</div><div class="finding neutral">required but not reached (rejected earlier)</div></div>')
    else:
        body_parts.append('<div class="stage"><div class="stage-label">Sandbox</div><div class="finding neutral">skipped (Track I, low risk)</div></div>')

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

    OUT.write_text(PAGE_HEAD.format(css=CSS, topbar=topbar("audit")) + body + PAGE_TAIL)
    print(f"wrote {OUT} ({len(records)} runs)")


if __name__ == "__main__":
    main()
