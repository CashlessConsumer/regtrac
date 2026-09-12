#!/usr/bin/env python3
"""RegTrac site builder: data/*.csv + content/*.md -> static HTML + DuckDB + llms.txt + sitemap."""
import csv, html, json, os, re, sqlite3, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://regtrac.cashlessconsumer.in"
AS_OF = "12 Sep 2026"
BUILD_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

TYPE_LABELS = {
    "statutory_core": "Statutory regulator",
    "statutory_adjacent": "Statutory · adjacent",
    "nonstatutory_context": "Non-statutory · context",
}
EVENT_TYPE_LABELS = {
    "statute": "Statute", "establishment": "Established", "transfer": "Transfer",
    "leadership": "Leadership", "reform": "Reform", "proposal": "Proposal",
    "sro_framework": "SRO framework",
}

def read_csv(name):
    with open(os.path.join(ROOT, "data", name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

REGS = read_csv("regulators.csv")
LEAD = read_csv("leadership.csv")
EVENTS = read_csv("events.csv")
EVENTS.sort(key=lambda e: e["date"], reverse=True)
REG_BY_ID = {r["id"]: r for r in REGS}

def read_md(id_):
    p = os.path.join(ROOT, "content", f"reg-{id_}.md")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()

def md_to_html(md, page_id):
    """Minimal markdown: ## headings, - lists, > quotes, **bold**, [links](url)."""
    out, i = [], 0
    lines = md.split("\n")
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("## "):
            out.append(f'<h2>{inline(html.escape(ln[3:]))}</h2>')
        elif ln.startswith("# "):
            pass  # h1 rendered from frontmatter
        elif ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:]); i += 1
            out.append(f'<blockquote><p>{inline(html.escape(" ".join(buf)))}</p></blockquote>')
            continue
        elif ln.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(html.escape(lines[i][2:]))}</li>"); i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif ln.strip() == "":
            pass
        elif ln.startswith("*(") and ln.endswith(")*"):
            out.append(f'<p class="asof">{inline(html.escape(ln[1:-1]))}</p>')
        else:
            out.append(f"<p>{inline(html.escape(ln))}</p>")
        i += 1
    return "\n".join(out)

def inline(t):
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" rel="noopener">\1</a>', t)
    return t

def esc(s):
    return html.escape(s or "", quote=True)

def nav(active):
    links = [("index.html", "RegTrac"), ("regulators.html", "Register"),
             ("timeline.html", "Timeline"), ("about.html", "About"),
             ("https://srotrac.cashlessconsumer.in", "SROTrac ↗")]
    items = "".join(
        f'<a href="{u}" {"class=\"active\"" if u == active else ""}'
        f'{" target=\"_blank\" rel=\"noopener\"" if u.startswith("http") else ""}>{esc(t)}</a>'
        for u, t in links)
    return f'''
<header>
  <div class="wrap nav">
    <a class="brand" href="index.html"><span class="eye">◉</span> RegTrac</a>
    <nav>{items}</nav>
  </div>
</header>'''

def footer():
    return f'''
<footer>
  <div class="wrap">
    <p><strong>RegTrac</strong> — statutory financial regulators of India, tracked by <a href="https://cashlessconsumer.in" rel="noopener">CashlessConsumer</a>.</p>
    <p>Layer 1 of the sousveillance stack: <a href="https://regtrac.cashlessconsumer.in">RegTrac</a> (rule-writers) · <a href="https://srotrac.cashlessconsumer.in">SROTrac</a> (rule-borrowers) · LobbyWatch (rule-buyers — planned). Open data: <code>data/*.csv</code> in the repo. Built {BUILD_UTC}; leadership positions as of {AS_OF}.</p>
  </div>
</footer>'''

def page(title, desc, body, active, extra_head=""):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/{active}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}/{active}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="css/style.css?v={BUILD_UTC}">
{extra_head}
</head>
<body>
{nav(active)}
<main>
{body}
</main>
{footer()}
</body>
</html>'''

def src_cell(l):
    if not l["source_url"]:
        return ""
    return f'<a href="{esc(l["source_url"])}" rel="noopener" title="Source">&#8599;</a>'

def leadership_table(reg_id):
    rows = [l for l in LEAD if l["regulator"] == reg_id]
    if not rows:
        return ""
    trs = "".join(
        f'<tr><td>{esc(l["role"])}</td><td><strong>{esc(l["name"])}</strong></td>'
        f'<td>{esc(l["since"])}</td><td>{esc(l["term_or_note"])}</td>'
        f'<td>{esc(l["predecessor"])}</td>'
        f'<td>{src_cell(l)}</td></tr>'
        for l in rows)
    return f'''<h2>Leadership</h2>
<div class="table-scroll"><table>
<thead><tr><th>Role</th><th>Name</th><th>Since</th><th>Note</th><th>Predecessor</th><th>Src</th></tr></thead>
<tbody>{trs}</tbody></table></div>
<p class="asof">Appointments as of {AS_OF}. Sources attached per row.</p>'''

def reg_page(r):
    rid, name = r["id"], r["name"]
    md = read_md(rid)
    body_md = md_to_html(md, rid) if md else ""
    if not md:
        facts = f'''<h2>Record</h2>
<ul>
<li><strong>Statute:</strong> {esc(r["statute"])}</li>
<li><strong>Established:</strong> {esc(r["established"])}</li>
<li><strong>Under:</strong> {esc(r["ministry"])}</li>
<li><strong>Mandate:</strong> {esc(r["mandate"])}</li>
<li><strong>Consumer grievance route:</strong> {esc(r["grievance"])}</li>
<li><strong>Site:</strong> <a href="{esc(r["website"])}" rel="noopener">{esc(r["website"])}</a></li>
</ul>'''
    else:
        facts = ""
    badge = TYPE_LABELS.get(r["type"], r["type"])
    head = f'''
<p class="crumbs"><a href="regulators.html">← Register</a></p>
<span class="badge b-{r["type"].replace("_", "-")}">{esc(badge)}</span>
<h1>{esc(name)}</h1>
<p class="dek">{esc(r["statute"])}</p>'''
    body = head + facts + leadership_table(rid) + body_md
    body += reg_crosslink(rid)
    return page(f"{name} — RegTrac",
                f"{name}: statute, powers, leadership, grievance routes and accountability watchpoints — tracked by RegTrac.",
                body, f"reg-{rid}.html")

def reg_crosslink(rid):
    if rid == "rbi":
        return '''<h2>Layer link</h2><p>The RBI <em>recognises</em> India's fintech SROs — FACE and UFF. Who sits inside them: <a href="https://srotrac.cashlessconsumer.in" target="_blank" rel="noopener">SROTrac</a>.</p>'''
    if rid == "sebi":
        return '''<h2>Layer link</h2><p>SEBI-recognised SROs (AMFI, ANMI, BASL) are in SROTrac's future scope: <a href="https://srotrac.cashlessconsumer.in" target="_blank" rel="noopener">SROTrac</a>.</p>'''
    return ""

def index_page():
    core = [r for r in REGS if r["type"] == "statutory_core"]
    rows = "".join(
        f'<tr><td><a href="reg-{r["id"]}.html"><strong>{esc(r["abbr"])}</strong></a></td>'
        f'<td>{esc(r["name"])}</td><td>{esc(r["statute"])}</td>'
        f'<td>{esc(r["established"])}</td></tr>' for r in core)
    recent = "".join(
        f'<li><span class="chip">{esc(EVENT_TYPE_LABELS.get(e["type"], e["type"]))}</span> '
        f'<strong>{e["date"]}</strong> — {esc(e["title"])}</li>'
        for e in EVENTS[:6])
    stats = f'''<div class="stats">
<div><b>{len(REGS)}</b><span>entities tracked</span></div>
<div><b>{len([r for r in REGS if r["type"] == "statutory_core"])}</b><span>statutory regulators</span></div>
<div><b>{len(LEAD)}</b><span>appointments logged</span></div>
<div><b>{len(EVENTS)}</b><span>timeline events</span></div>
</div>'''
    body = f'''
<section class="hero">
  <p class="kicker">CashlessConsumer · a sousveillance project</p>
  <h1>The watchers,<br>watched.</h1>
  <p class="dek">RegTrac tracks the statutory regulators of India's financial sector — their statutes, powers, leadership appointments, grievance machinery and accountability gaps. Surveillance is watching citizens; <em>sousveillance</em> is citizens watching back.</p>
  {stats}
</section>
<section>
  <h2>The sousveillance stack</h2>
  <div class="layers">
    <a class="layer live" href="https://regtrac.cashlessconsumer.in"><b>RegTrac</b><span>Rule-writers — statutory regulators</span><em>live</em></a>
    <a class="layer live" href="https://srotrac.cashlessconsumer.in" target="_blank" rel="noopener"><b>SROTrac</b><span>Rule-borrowers — recognised SROs and their rosters</span><em>live</em></a>
    <a class="layer planned" href="about.html#stack"><b>LobbyWatch</b><span>Rule-buyers — consultations, access, revolving doors</span><em>planned</em></a>
  </div>
</section>
<section>
  <h2>Register — statutory regulators</h2>
  <div class="table-scroll"><table>
  <thead><tr><th></th><th>Name</th><th>Statute</th><th>Est.</th></tr></thead>
  <tbody>{rows}</tbody></table></div>
  <p><a href="regulators.html">Full register — including adjacent statutory bodies and non-statutory context →</a></p>
</section>
<section>
  <h2>Recent</h2>
  <ul class="recent">{recent}</ul>
  <p><a href="timeline.html">Full timeline →</a></p>
</section>'''
    return page("RegTrac — India's financial regulators, tracked",
                "RegTrac: a public register of India's statutory financial regulators — RBI, SEBI, IRDAI, PFRDA, IBBI, IFSCA, NABARD — statutes, leadership, powers and accountability gaps. A CashlessConsumer sousveillance project.",
                body, "index.html")

def regulators_page():
    chips = [("all", "All", True)] + [(t, l, False) for t, l in TYPE_LABELS.items()]
    chip_html = "".join(
        f'<button class="fchip{" on" if d else ""}" data-f="{t}" onclick="filterType(this)">{esc(l)}</button>'
        for t, l, d in chips)
    rows = ""
    for r in REGS:
        has_page = bool(read_md(r["id"]))
        name_cell = (f'<a href="reg-{r["id"]}.html"><strong>{esc(r["abbr"])}</strong></a> · {esc(r["name"])}'
                     if has_page else f'<a href="reg-{r["id"]}.html">{esc(r["name"])}</a>')
        rows += (f'<tr data-t="{esc(r["type"])}">'
                 f'<td>{name_cell}</td><td>{esc(r["statute"])}</td>'
                 f'<td>{esc(r["established"])}</td><td>{esc(r["ministry"])}</td>'
                 f'<td><span class="badge b-{r["type"].replace("_", "-")}">{esc(TYPE_LABELS[r["type"]])}</span></td></tr>')
    script = '''<script>
function filterType(btn){
  document.querySelectorAll('.fchip').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  const f=btn.dataset.f;
  document.querySelectorAll('#regtable tbody tr').forEach(tr=>{
    tr.style.display = (f==='all'||tr.dataset.t===f)?'':'none';
  });
}
</script>'''
    body = f'''
<h1>Register</h1>
<p class="dek">Every financial-sector entity with rule-writing power over the public — statutory core first, adjacent statutory bodies next, non-statutory context flagged.</p>
<div class="chips">{chip_html}</div>
<div class="table-scroll"><table id="regtable">
<thead><tr><th>Entity</th><th>Statute / basis</th><th>Est.</th><th>Under</th><th>Type</th></tr></thead>
<tbody>{rows}</tbody></table></div>
{script}'''
    return page("Register — RegTrac",
                "The full RegTrac register: statutory regulators, adjacent statutory bodies, and non-statutory context entities of Indian finance.",
                body, "regulators.html")

def timeline_page():
    chips = [("all", "All", True)] + [(t, l, False) for t, l in EVENT_TYPE_LABELS.items()]
    chip_html = "".join(
        f'<button class="fchip{" on" if d else ""}" data-f="{t}" onclick="filterType(this)">{esc(l)}</button>'
        for t, l, d in chips)
    rows = ""
    for e in EVENTS:
        src = f' <a href="{esc(e["source_url"])}" rel="noopener">↗</a>' if e["source_url"] else ""
        actor = REG_BY_ID.get(e["actor"], {}).get("abbr", e["actor"])
        rows += (f'<tr data-t="{esc(e["type"])}"><td>{e["date"]}</td>'
                 f'<td><a href="reg-{esc(e["actor"])}.html">{esc(actor)}</a></td>'
                 f'<td>{esc(e["title"])}{src}</td>'
                 f'<td><span class="chip">{esc(EVENT_TYPE_LABELS.get(e["type"], e["type"]))}</span></td></tr>')
    script = '''<script>
function filterType(btn){
  document.querySelectorAll('.fchip').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  const f=btn.dataset.f;
  document.querySelectorAll('#evtable tbody tr').forEach(tr=>{
    tr.style.display = (f==='all'||tr.dataset.t===f)?'':'none';
  });
}
</script>'''
    body = f'''
<h1>Timeline</h1>
<p class="dek">Statutes, establishments, transfers, leadership churn and reforms — the making of India's financial rule-writers.</p>
<div class="chips">{chip_html}</div>
<div class="table-scroll"><table id="evtable">
<thead><tr><th>Date</th><th>Entity</th><th>Event</th><th>Type</th></tr></thead>
<tbody>{rows}</tbody></table></div>
{script}'''
    return page("Timeline — RegTrac",
                "Chronology of Indian financial regulation: statutes, establishments, leadership changes and reforms, with sources.",
                body, "timeline.html")

ABOUT_MD = '''## Scope

RegTrac tracks entities with statutory rule-writing power over India's financial sector: the seven core regulators (RBI, SEBI, IRDAI, PFRDA, IBBI, IFSCA, NABARD), adjacent statutory bodies (DICGC, NHB, SIDBI, NFRA), and non-statutory context entities that shape policy without a statute (FSDC, NPCI).

Out of scope by design: self-regulatory organisations — those live in SROTrac. Ministry-level policy making (Department of Economic Affairs, Department of Financial Services, MCA) enters RegTrac only where it touches regulator appointments; the LobbyWatch layer will own it properly.

## Method

- The register is a small, auditable CSV — one row per entity — with the statute, establishing date, parent ministry, mandate and consumer grievance route.
- Leadership rows are added only with an appointment date and a source URL. Claims without a source stay out.
- The timeline is one row per event, same rule.
- Everything is regenerated from data by a single build script; the site is static HTML with no trackers, no cookies, no JavaScript dependencies.

## Caveats

- Leadership positions are stated **as of {as_of}** and will drift; rows carry their source so the next refresh can re-verify.
- "Statutory adjacent" bodies (DICGC, NHB, SIDBI, NFRA) are institutions with statutory foundations but narrower or shifted regulatory roles (e.g., HFC regulation moved from NHB to RBI in 2019).
- FSDC and NPCI are listed as context precisely because they lack statutes — the most consequential coordination in Indian finance happens in a body with no statutory foundation, and the payment rails are run by an industry-owned company. Both facts belong on the record, not in a footnote.

## The stack

RegTrac is layer one of a three-layer sousveillance stack for Indian financial policy making:

1. **RegTrac** (this site) — the *rule-writers*: statutory regulators, their powers, appointments, consultations and grievance machinery.
2. **SROTrac** — the *rule-borrowers*: RBI-recognised self-regulatory organisations and — the part that matters — their member rosters, where industry consensus on fees and conduct actually forms.
3. **LobbyWatch** (planned) — the *rule-buyers*: who submits on consultations, who meets whom, the revolving door between regulator and regulated, industry-association access to FSDC and ministries.

The stack's promise is the join: a consultation submission on an RBI draft (LobbyWatch), cross-referenced against SRO membership (SROTrac), cross-referenced against the regulatory change that followed (RegTrac). Each layer alone is a directory; together they are a map of how financial policy gets made in India — and for whom.

## Open data

`data/regulators.csv`, `data/leadership.csv`, `data/events.csv` and a DuckDB database ship in the repository, plus an `llms.txt` for machine readers. Take it, fork it, build on it — attribution appreciated.

## Colophon

Built by CashlessConsumer — a consumer collective working on digital payments and fintech since 2016. Sister projects: [SROTrac](https://srotrac.cashlessconsumer.in), [DPI Watch](https://dpiwatch.in). Corrections: raise an issue on the repository.'''

def about_page():
    md = ABOUT_MD.replace("{as_of}", AS_OF)
    body = f'''<h1>About</h1>
<p class="dek">What RegTrac tracks, how, and why.</p>
{md_to_html(md, "about")}'''
    return page("About — RegTrac",
                "Scope, method and caveats of RegTrac — the statutory-regulator layer of CashlessConsumer's financial-sector sousveillance stack.",
                body, "about.html")

def write_static():
    with open(os.path.join(ROOT, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: " + BASE + "/sitemap.xml\n")
    ids = [r["id"] for r in REGS]
    pages = ["index.html", "regulators.html", "timeline.html", "about.html"] + [f"reg-{i}.html" for i in ids]
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for p in pages:
            f.write(f"  <url><loc>{BASE}/{p}</loc></url>\n")
        f.write("</urlset>\n")
    core_list = "\n".join(f"- {r['name']} ({r['abbr']}): {r['statute']}" for r in REGS)
    with open(os.path.join(ROOT, "llms.txt"), "w") as f:
        f.write(f"""# RegTrac

> Public register of India's statutory financial regulators — statutes, leadership appointments, powers, grievance routes and accountability gaps. By CashlessConsumer. Leadership as of {AS_OF}.

Part of a three-layer sousveillance stack: RegTrac (rule-writers), SROTrac (rule-borrowers, https://srotrac.cashlessconsumer.in), LobbyWatch (rule-buyers, planned).

## Pages

- [Index]({BASE}/index.html): overview, stats, stack, register of core regulators
- [Register]({BASE}/regulators.html): all {len(REGS)} entities with type filters
- [Timeline]({BASE}/timeline.html): {len(EVENTS)} sourced events
- [About]({BASE}/about.html): scope, method, caveats, the stack

## Register

{core_list}

## Data

CSVs + DuckDB in the repository: data/regulators.csv, data/leadership.csv, data/events.csv.
""")
    with open(os.path.join(ROOT, "llms-full.txt"), "w") as f:
        f.write(f"# RegTrac — full text\n\nLeadership as of {AS_OF}. Built {BUILD_UTC}.\n\n")
        f.write("## Register\n\n")
        for r in REGS:
            f.write(f"### {r['name']} ({r['abbr']})\nType: {TYPE_LABELS[r['type']]}. Statute: {r['statute']}. Established: {r['established']}. Under: {r['ministry']}.\nMandate: {r['mandate']}\nGrievance: {r['grievance']}\nSite: {r['website']}\n\n")
        f.write("## Leadership\n\n")
        for l in LEAD:
            f.write(f"- {REG_BY_ID[l['regulator']]['abbr']} {l['role']}: {l['name']} since {l['since']} {('('+l['term_or_note']+')') if l['term_or_note'] else ''}. Source: {l['source_url']}\n")
        f.write("\n## Timeline\n\n")
        for e in EVENTS:
            f.write(f"- {e['date']} {REG_BY_ID[e['actor']]['abbr']}: {e['title']}\n")
        f.write("\n" + ABOUT_MD.replace("{as_of}", AS_OF) + "\n")
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (1200, 630), "#101826")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 1200, 8], fill="#d97706")
        try:
            big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 96)
            small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
            tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except OSError:
            big = small = tiny = ImageFont.load_default()
        d.text((80, 170), "RegTrac", font=big, fill="#faf7f2")
        d.text((84, 300), "The watchers, watched.", font=small, fill="#d97706")
        d.text((84, 380), "Statutory financial regulators of India — statutes, powers,", font=tiny, fill="#9fb0c7")
        d.text((84, 420), "appointments, grievance machinery, accountability gaps.", font=tiny, fill="#9fb0c7")
        d.text((84, 540), "regtrac.cashlessconsumer.in  ·  CashlessConsumer", font=tiny, fill="#5c6f8a")
        img.save(os.path.join(ROOT, "og.png"))
        print("og.png written")
    except Exception as e:
        print("og.png skipped:", e)

def build_db():
    try:
        import duckdb
    except ImportError:
        print("duckdb module not available — building sqlite fallback")
        con = sqlite3.connect(os.path.join(ROOT, "data", "regtrac.db"))
        for name, rows in (("regulators", REGS), ("leadership", LEAD), ("events", EVENTS)):
            cols = rows[0].keys()
            con.execute(f"DROP TABLE IF EXISTS {name}")
            con.execute(f"CREATE TABLE {name} ({', '.join(f'{c} VARCHAR' for c in cols)})")
            con.executemany(
                f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})",
                [[r[c] for c in cols] for r in rows])
        con.commit(); con.close()
        print("data/regtrac.db (sqlite) written")
        return
    path = os.path.join(ROOT, "data", "regtrac.duckdb")
    if os.path.exists(path):
        os.remove(path)
    con = duckdb.connect(path)
    for name, rows in (("regulators", REGS), ("leadership", LEAD), ("events", EVENTS)):
        cols = list(rows[0].keys())
        con.execute(f"CREATE TABLE {name} ({', '.join(f'{c} VARCHAR' for c in cols)})")
        con.executemany(f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})",
                        [[r[c] for c in cols] for r in rows])
    con.close()
    print("data/regtrac.duckdb written")

def main():
    pages = {"index.html": index_page(), "regulators.html": regulators_page(),
             "timeline.html": timeline_page(), "about.html": about_page()}
    for r in REGS:
        pages[f"reg-{r['id']}.html"] = reg_page(r)
    for name, content in pages.items():
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote", name)
    write_static()
    build_db()
    print(f"done: {len(pages)} pages, {len(REGS)} entities, {len(LEAD)} appointments, {len(EVENTS)} events")

if __name__ == "__main__":
    main()
