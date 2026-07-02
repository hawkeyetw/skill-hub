"""Shared CSS + header/nav for catalog.html and audit.html - kept in one place so
the two pages don't visually drift apart.

Design tokens below were extracted from https://www.skillhub.club/'s actual
compiled Tailwind CSS + rendered HTML (fetched and analyzed via Codex, not
eyeballed from screenshots - an earlier pass guessed a cream background and an
always-on drop-shadow "neo-brutalist" card style from a couple of screenshots,
both wrong: the real background is white, and shadows only appear on :hover
alongside a translate-y lift). Only the visual language was copied, not that
site's feature set (AI search, leaderboards, KOL pages, login, etc. are out of
scope - see .trellis/spec/architecture/04-audience-distribution-channels.md).

Real tokens (light theme): background #FFFFFF, foreground/text #000000,
card #FFFFFF, border #000000 (2px, radius 0), border-light #E5E5E5,
secondary/hover-bg #F5F5F5, muted-text #666666, CTA green #10B981
(hover #059669), amber #F59E0B (badges), font family "hyperlegible" with
system-ui/-apple-system/sans-serif fallback, uppercase+tracking-wider labels.
"""

CSS = """
  :root {
    --bg: #ffffff;
    --ink: #000000;
    --border: #000000;
    --border-light: #e5e5e5;
    --secondary: #f5f5f5;
    --muted: #666666;
    --green: #10b981;
    --green-hover: #059669;
    --amber: #f59e0b;
    --red: #dc2626;
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Atkinson Hyperlegible", "Segoe UI", system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--ink);
    max-width: 1040px; margin: 0 auto; padding: 0 20px 100px;
  }
  a { color: inherit; }
  .topbar {
    position: sticky; top: 0; z-index: 10; background: var(--bg);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    height: 52px; margin: 0 -20px 28px; padding: 0 20px;
  }
  .logo { font-weight: 800; font-size: 1rem; letter-spacing: -0.01em; display: flex; align-items: center; gap: 8px; text-transform: uppercase; }
  .logo .dot { width: 8px; height: 8px; background: var(--green); border: 1.5px solid var(--border); display: inline-block; }
  .navlinks { display: flex; gap: 4px; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.04em; }
  .navlinks a { padding: 6px 12px; border: 2px solid transparent; text-decoration: none; text-transform: uppercase; }
  .navlinks a.active { border-color: var(--border); }
  .navlinks a:hover:not(.active) { background: var(--secondary); }
  h1 { font-size: 1.7rem; margin: 18px 0 6px; letter-spacing: -0.02em; font-weight: 800; }
  .meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 22px; line-height: 1.6; }
  .meta code { background: var(--secondary); border: 1px solid var(--border-light); padding: 1px 5px; }
  .stats { display: flex; gap: 0; margin-bottom: 24px; flex-wrap: wrap; border: 2px solid var(--border); width: fit-content; }
  .stat { padding: 10px 22px; text-align: center; border-right: 2px solid var(--border); }
  .stat:last-child { border-right: none; }
  .stat .n { font-size: 1.5rem; font-weight: 800; line-height: 1.1; }
  .stat .label { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
  #search {
    width: 100%; padding: 11px 16px; font-size: 0.92rem;
    border: 2px solid var(--border); background: #fff; margin-bottom: 22px;
  }
  #search:focus { outline: none; background: var(--secondary); }
  .empty { color: var(--muted); font-style: italic; text-align: center; padding: 50px 0; border: 2px dashed var(--border-light); }
"""

def topbar(active: str) -> str:
    def cls(name):
        return "active" if name == active else ""
    return f"""<div class="topbar">
  <div class="logo"><span class="dot"></span>SKILL-HUB</div>
  <div class="navlinks">
    <a href="catalog.html" class="{cls('catalog')}">Catalog</a>
    <a href="audit.html" class="{cls('audit')}">Review Pipeline</a>
  </div>
</div>
"""
