#!/usr/bin/env python3
"""Render blog/posts/*.md into the RegTrac briefs layer.

Produces, from the same Markdown the swarm writes:

  blog/index.html          cross-regulator stream (published + in review)
  blog/reg-<rid>.html      per-regulator stream, one for every entity in the register
  blog/<slug>.html         the post itself
  blog/feed.xml            RSS 2.0 for published briefs

Drafts never render. Runs after build.py; reuses that module's page/nav/CSS helpers
so the editorial layer cannot drift away from the site chrome.
"""
import importlib.util
import os
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xesc

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import frontmatter  # noqa: E402

_spec = importlib.util.spec_from_file_location("regtrac_build", os.path.join(_HERE, "build.py"))
_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_build)

ROOT = _build.ROOT
BASE = _build.BASE
REG_BY_ID = _build.REG_BY_ID
REGS = _build.REGS
page = _build.page
esc = _build.esc
md_to_html = _build.md_to_html
TYPE_LABELS = _build.TYPE_LABELS

POSTS_DIR = os.path.join(ROOT, "blog", "posts")
BLOG_DIR = os.path.join(ROOT, "blog")
BUILD_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

BLOG_CSS = """
.crumbs{margin:0 0 14px;font-size:.9rem}
.crumbs a{color:var(--accent)}
.brief-head{max-width:780px;margin:0 auto 8px}
.stream{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin-top:20px}
.brief-card{background:#fff;border:1px solid #e7e2d8;border-radius:10px;padding:18px 20px}
.brief-card .meta{font-size:.78rem;color:#8a8375;letter-spacing:.02em;text-transform:uppercase;margin-bottom:8px}
.brief-card h3{margin:0 0 8px;font-size:1.06rem;line-height:1.35}
.brief-card h3 a{color:var(--ink);text-decoration:none}
.brief-card h3 a:hover{color:var(--accent)}
.brief-card p{margin:0;color:#57534e;font-size:.9rem}
.brief-card .reg{display:inline-block;font-size:.72rem;font-weight:600;color:var(--accent);border:1px solid #e7e2d8;border-radius:20px;padding:1px 9px;margin-bottom:8px}
.sbadge{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;border-radius:4px;padding:2px 7px;margin-left:8px}
.s-published{background:#dcfce7;color:#166534}
.s-review{background:#fef3c7;color:#92400e}
.post-full{max-width:780px;margin:0 auto;background:#fff;border:1px solid #e7e2d8;border-radius:10px;padding:32px 36px}
.post-full .byline{font-size:.82rem;color:#8a8375;margin:0 0 20px;border-bottom:1px solid #efe9df;padding-bottom:12px}
.post-full h1{margin:0 0 12px;font-size:1.75rem;line-height:1.25}
.post-full h2{margin:28px 0 10px;font-size:1.16rem;border-top:1px solid #efe9df;padding-top:18px}
.post-full ul{padding-left:20px}
.post-full li{margin:0 0 9px;line-height:1.55}
.post-full p{line-height:1.6}
.post-full em{color:#6b6559}
.post-full code{background:#f3efe6;padding:1px 5px;border-radius:4px;font-size:.86em}
.post-full a{color:var(--accent)}
.personas{font-size:.76rem;color:#8a8375;margin-top:26px;border-top:1px solid #efe9df;padding-top:12px}
.empty{padding:26px 0;color:#8a8375}
"""


def load_posts(include_drafts=False):
    if not os.path.isdir(POSTS_DIR):
        return []
    posts = []
    for name in sorted(os.listdir(POSTS_DIR)):
        if not name.endswith(".md"):
            continue
        meta, body = frontmatter.parse(os.path.join(POSTS_DIR, name))
        status = str(meta.get("status", "draft"))
        if status == "draft" and not include_drafts:
            continue
        posts.append({
            "slug": name[:-3],
            "meta": meta,
            "body": body,
            "html": md_to_html(body, name[:-3]),
            "date": str(meta.get("date", "")),
            "regulator": str(meta.get("regulator", "")),
            "status": status,
        })
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def reg_label(rid):
    r = REG_BY_ID.get(rid)
    return r["abbr"] if r else rid.upper()


def card(p):
    rid = p["regulator"]
    badge = f'<span class="reg">{esc(reg_label(rid))}</span>' if rid else ""
    sb = ("" if p["status"] == "published"
          else f'<span class="sbadge s-{esc(p["status"])}">{esc(p["status"])}</span>')
    return f'''<article class="brief-card">
{badge}{sb}
<div class="meta">{esc(p["date"])} · {esc(str(p["meta"].get("event_type", "")))}</div>
<h3><a href="{esc(p['slug'])}.html">{esc(str(p["meta"].get("title", p["slug"])))}</a></h3>
<p>{esc(str(p["meta"].get("summary", "")))}</p>
</article>'''


def stream(posts):
    if not posts:
        return '<p class="empty">No briefs published yet. The swarm composes a brief per regulator as the register changes.</p>'
    return '<div class="stream">' + "".join(card(p) for p in posts) + "</div>"


def index(posts):
    chips = "".join(
        f'<a class="fchip" href="reg-{esc(r["id"])}.html">{esc(r["abbr"])}</a>' for r in REGS)
    ynav = " ".join(f'<a href="{y}.html">{y}</a>'
                    for y in sorted({p["date"][:4] for p in posts}, reverse=True))
    body = f'''<section class="page-head">
<p class="crumbs"><a href="../index.html">← RegTrac</a></p>
<h1>RegTrac Blog</h1>
<p class="lede">A weekly edition from the desk on the most consequential development across the
register, plus one brief per regulator: what changed, why it matters, who it affects, what to
watch — every line carrying its own source. Gated before publication.</p>
<div class="chips" style="margin:14px 0 4px">{chips}</div>
<p class="archnav" style="margin:12px 0 0;font-size:.9rem">Editions: {ynav} · <a href="archive.html">Full archive</a> · <a href="feed.xml">RSS</a></p>
</section>
{stream(posts[:12])}'''
    return page("Blog — RegTrac",
                "Per-regulator briefs from the RegTrac editorial swarm: what changed, why it matters, who is affected, what to watch, and the evidence.",
                body, "blog/index.html", depth=1)


def reg_stream(reg, posts):
    rid, name, abbr = reg["id"], reg["name"], reg["abbr"]
    body = f'''<section class="page-head">
<p class="crumbs"><a href="index.html">← All briefs</a> · <a href="../reg-{esc(rid)}.html">Register entry</a></p>
<h1>{esc(name)} — briefs</h1>
<p class="lede">{esc(TYPE_LABELS.get(reg["type"], reg["type"]))} · {esc(reg["statute"])}</p>
</section>
{stream(posts)}'''
    return page(f"{abbr} briefs — RegTrac",
                f"RegTrac briefs for {name}: changes in leadership, law and enforcement, and the accountability gaps to watch.",
                body, f"blog/reg-{rid}.html", depth=1)


def post_page(p):
    rid = p["regulator"]
    r = REG_BY_ID.get(rid)
    personas = p["meta"].get("personas") or []
    if not isinstance(personas, list):
        personas = [personas]
    signoffs = " · ".join(f"{esc(x)} ✓" for x in personas) if personas else "—"
    crumb_reg = (f'<a href="reg-{esc(rid)}.html">{esc(reg_label(rid))} briefs</a> &middot; '
                 f'<a href="../reg-{esc(rid)}.html">register entry</a>'
                 if r else '<a href="index.html">Briefs</a>')
    sb = ("" if p["status"] == "published"
          else f'<span class="sbadge s-{esc(p["status"])}">{esc(p["status"])}</span>')
    body = f'''<article class="post-full">
<p class="crumbs">{crumb_reg}</p>
<div class="meta">{esc(p["date"])} · {esc(str(p["meta"].get("event_type", "")))} {sb}</div>
{p["html"]}
<p class="personas">Editorial swarm: {signoffs} · gated by <code>scripts/editorial.py</code> on {BUILD_UTC}.</p>
</article>
<p style="max-width:780px;margin:14px auto 0"><a href="index.html">← All briefs</a></p>'''
    return page(str(p["meta"].get("title", p["slug"])),
                str(p["meta"].get("summary", "")),
                body, f"blog/{p['slug']}.html", depth=1)



ARCHIVE_CSS = """<style>
.achips{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 4px}
.achip{font:inherit;font-size:.8rem;border:1px solid #e7e2d8;border-radius:20px;padding:3px 12px;color:inherit;text-decoration:none;cursor:pointer;background:#fff}
.achip[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.arch-year{font-size:1.25rem;margin:30px 0 6px;border-bottom:2px solid var(--accent);padding-bottom:6px}
.arch-year a{color:inherit;text-decoration:none}
.arch-count{color:#8a8375;font-weight:400;font-size:.85rem}
.arch-month{font-variant:small-caps;letter-spacing:.05em;color:#8a8375;margin:18px 0 8px;font-size:1.05rem}
.brief-card.hide{display:none}
</style>
<script>
document.addEventListener('click',function(e){
  var b=e.target.closest('.achip');
  if(!b||!b.closest('#achips'))return;
  var wrap=b.closest('#achips');
  var on=b.getAttribute('aria-pressed')==='true';
  wrap.querySelectorAll('.achip').forEach(function(x){x.setAttribute('aria-pressed','false')});
  if(!on)b.setAttribute('aria-pressed','true');
  var cat=on?null:b.dataset.cat;
  document.querySelectorAll('[data-pcat]').forEach(function(c){
    c.classList.toggle('hide',cat!==null&&c.dataset.pcat!==cat);
  });
});
</script>"""


def pcat(p):
    v = str(p["meta"].get("event_type", "") or "").strip().lower()
    return v or "note"


def acard(p):
    rid = p["regulator"]
    badge = f'<span class="reg">{esc(reg_label(rid))}</span>' if rid else ""
    sb = ("" if p["status"] == "published"
          else f'<span class="sbadge s-{esc(p["status"])}">{esc(p["status"])}</span>')
    return f'''<article class="brief-card" data-pcat="{esc(pcat(p))}">
{badge}{sb}
<div class="meta">{esc(p["date"])} · {esc(pcat(p))}</div>
<h3><a href="{esc(p['slug'])}.html">{esc(str(p["meta"].get("title", p["slug"])))}</a></h3>
<p>{esc(str(p["meta"].get("summary", "")))}</p>
</article>'''


def achips(cats):
    out = '<button class="achip" data-cat="" aria-pressed="true">All</button>'
    for c in cats:
        out += f'<button class="achip" data-cat="{esc(c)}" aria-pressed="false">{esc(c)}</button>'
    return out


def group_months(year_posts):
    months = {}
    for p in year_posts:
        months.setdefault(p["date"][5:7], []).append(p)
    return [(m, months[m]) for m in sorted(months, reverse=True)]


def year_sections(posts, link_years=True):
    import calendar
    sections = ""
    for y in sorted({p["date"][:4] for p in posts}, reverse=True):
        yp = [p for p in posts if p["date"][:4] == y]
        head = f'<a href="{y}.html">{y}</a>' if link_years else y
        sections += (f'<h2 class="arch-year">{head} '
                     f'<span class="arch-count">· {len(yp)} post{"s" if len(yp) != 1 else ""}</span></h2>')
        for m, mp in group_months(yp):
            sections += (f'<h3 class="arch-month">{calendar.month_name[int(m)]} {y}</h3>'
                         f'<div class="stream">{"".join(acard(p) for p in mp)}</div>')
    return sections


def archive_page(posts, cats, year=None):
    import calendar
    shown = [p for p in posts if not year or p["date"][:4] == year]
    title = f"RegTrac Blog — Archive {year}" if year else "RegTrac Blog — Archive"
    ynav = " ".join(f'<a class="achip" href="{y}.html">{y}</a>'
                    for y in sorted({p["date"][:4] for p in posts}, reverse=True))
    body = f'''<section class="page-head">
<p class="crumbs"><a href="../index.html">← RegTrac</a></p>
<h1>{esc(title)}</h1>
<p class="lede">Every edition since launch, grouped by month. {len(shown)} post{"s" if len(shown) != 1 else ""}{f" in {year}" if year else ""}.</p>
<div class="achips" id="achips">{achips(cats)}</div>
<p style="margin:10px 0 0;font-size:.9rem">Years: {ynav} · <a href="index.html">Latest</a> · <a href="feed.xml">RSS</a></p>
</section>
<section style="max-width:1000px;margin:0 auto;padding:0 20px">{year_sections(shown, link_years=not year)}</section>'''
    return page(title, "Archive of RegTrac briefs and weekly editions, grouped by year and month.",
                body, "blog/index.html", extra_head=ARCHIVE_CSS, depth=1)


def patch_sitemap(posts):
    sm_path = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(sm_path):
        return
    txt = open(sm_path, encoding="utf-8").read()
    years = sorted({p["date"][:4] for p in posts}, reverse=True)
    add = ""
    for pth in ["blog/archive.html"] + [f"blog/{y}.html" for y in years]:
        loc = f"<loc>{BASE}/{pth}</loc>"
        if loc not in txt:
            add += f'<url>{loc}<changefreq>monthly</changefreq><priority>0.5</priority></url>'
    if add and "</urlset>" in txt:
        open(sm_path, "w", encoding="utf-8").write(txt.replace("</urlset>", add + "</urlset>"))


def feed(posts):
    pubs = [p for p in posts if p["status"] == "published"]
    items = ""
    for p in pubs:
        link = f"{BASE}/blog/{p['slug']}.html"
        try:
            pub = datetime.strptime(p["date"], "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")
        except ValueError:
            pub = ""
        items += (f"\n  <item>\n    <title>{xesc(str(p['meta'].get('title', p['slug'])))}</title>\n"
                  f"    <link>{link}</link>\n    <guid isPermaLink=\"true\">{link}</guid>\n"
                  f"    <pubDate>{pub}</pubDate>\n"
                  f"    <category>{xesc(reg_label(p['regulator']))}</category>\n"
                  f"    <description>{xesc(str(p['meta'].get('summary', '')))}</description>\n  </item>")
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>RegTrac Blog</title>
  <link>{BASE}/blog/</link>
  <description>Per-regulator briefs on India's statutory financial regulators.</description>
  <language>en-in</language>
  <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>{items}
</channel></rss>
'''


def main():
    os.makedirs(BLOG_DIR, exist_ok=True)
    posts = load_posts()
    by_reg = {}
    for p in posts:
        by_reg.setdefault(p["regulator"], []).append(p)

    written = []
    with open(os.path.join(BLOG_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index(posts))
    written.append("blog/index.html")

    for r in REGS:
        path = os.path.join(BLOG_DIR, f"reg-{r['id']}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(reg_stream(r, by_reg.get(r["id"], [])))
        written.append(f"blog/reg-{r['id']}.html")

    for p in posts:
        with open(os.path.join(BLOG_DIR, f"{p['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(post_page(p))
        written.append(f"blog/{p['slug']}.html")

    with open(os.path.join(BLOG_DIR, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(feed(posts))

    cats = sorted({pcat(p) for p in posts})
    years = sorted({p["date"][:4] for p in posts}, reverse=True)
    with open(os.path.join(BLOG_DIR, "archive.html"), "w", encoding="utf-8") as f:
        f.write(archive_page(posts, cats))
    written.append("blog/archive.html")
    for y in years:
        with open(os.path.join(BLOG_DIR, f"{y}.html"), "w", encoding="utf-8") as f:
            f.write(archive_page(posts, cats, year=y))
        written.append(f"blog/{y}.html")
    patch_sitemap(posts)

    css_path = os.path.join(ROOT, "css", "style.css")
    if os.path.exists(css_path):
        css = open(css_path, encoding="utf-8").read()
        if ".brief-card" not in css:
            with open(css_path, "a", encoding="utf-8") as f:
                f.write("\n" + BLOG_CSS)

    covered = sum(1 for r in REGS if by_reg.get(r["id"]))
    print(f"blog: {len(posts)} post page(s), {len(REGS)} regulator stream(s) "
          f"({covered} with briefs), feed.xml, index, archive — {len(written)} files")


if __name__ == "__main__":
    main()
