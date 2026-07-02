"""Shared CSS + header/nav for catalog.html and audit.html - kept in one place so
the two pages don't visually drift apart. Style is deliberately modeled on
https://www.skillhub.club/ (bold black borders, cream background, sharp corners,
hard drop-shadow cards, orange accent) per explicit user request - only the visual
language was copied, not that site's feature set (AI search, leaderboards, KOL
pages, login, etc. are all out of scope here, see
.trellis/spec/architecture/04-audience-distribution-channels.md for what this
Phase-1 static portal is actually meant to do).
"""

CSS = """
  :root {
    --bg: #faf6ef;
    --ink: #14120f;
    --border: #14120f;
    --accent: #ff6a3d;
    --green: #1a7f37;
    --red: #d1242f;
    --amber: #bf6a02;
    --muted: #6b6558;
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Helvetica Neue", Arial, "PingFang SC", sans-serif;
    background: var(--bg); color: var(--ink);
    max-width: 980px; margin: 0 auto; padding: 28px 20px 100px;
  }
  a { color: inherit; }
  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    border: 2px solid var(--border); background: #fff;
    padding: 12px 18px; margin-bottom: 22px; flex-wrap: wrap; gap: 12px;
    box-shadow: 4px 4px 0 var(--border);
  }
  .logo { font-weight: 800; font-size: 1.15rem; letter-spacing: -0.02em; display: flex; align-items: center; gap: 8px; }
  .logo .dot { width: 10px; height: 10px; background: var(--accent); border: 2px solid var(--border); display: inline-block; }
  .navlinks { display: flex; gap: 4px; font-size: 0.85rem; font-weight: 600; }
  .navlinks a { padding: 6px 12px; border: 2px solid transparent; text-decoration: none; }
  .navlinks a.active { border-color: var(--border); background: var(--bg); }
  .navlinks a:hover:not(.active) { border-color: #ddd6c8; }
  h1 { font-size: 1.7rem; margin: 6px 0 4px; letter-spacing: -0.02em; }
  .meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 22px; line-height: 1.6; }
  .meta code { background: #fff; border: 1px solid #ddd6c8; padding: 1px 5px; }
  .stats { display: flex; gap: 14px; margin-bottom: 24px; flex-wrap: wrap; }
  .stat {
    border: 2px solid var(--border); background: #fff; padding: 10px 18px;
    box-shadow: 3px 3px 0 var(--border); text-align: center; min-width: 120px;
  }
  .stat .n { font-size: 1.6rem; font-weight: 800; line-height: 1.1; }
  .stat .label { font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
  #search {
    width: 100%; padding: 12px 16px; font-size: 0.95rem;
    border: 2px solid var(--border); background: #fff; margin-bottom: 22px;
  }
  #search:focus { outline: none; box-shadow: 3px 3px 0 var(--border); }
  .empty { color: var(--muted); font-style: italic; text-align: center; padding: 50px 0; border: 2px dashed #ddd6c8; }
"""

def topbar(active: str) -> str:
    def cls(name):
        return "active" if name == active else ""
    return f"""<div class="topbar">
  <div class="logo"><span class="dot"></span>SKILL-HUB</div>
  <div class="navlinks">
    <a href="catalog.html" class="{cls('catalog')}">CATALOG</a>
    <a href="audit.html" class="{cls('audit')}">REVIEW PIPELINE</a>
  </div>
</div>
"""
