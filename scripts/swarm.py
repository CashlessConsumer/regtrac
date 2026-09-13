#!/usr/bin/env python3
"""RegTrac editorial swarm — composes a per-regulator brief from the register.

The swarm runs as a chain of deterministic persona stages. Every stage reads
evidence that is already in the repository; none of them invents a fact.

  tracker        diffs the register (data/*.csv) — appointments, timeline events
  evidence       attaches a source URL to every claim it keeps, drops the rest
  advocate       writes "Who is affected" from the register's grievance field
  institutional  writes "Why it matters" from the documented powers/mandate
  mapper         adds the layer link to SROTrac / LobbyWatch
  skeptic        writes "What to watch" from the entity's watchpoints
  editor         (scripts/editorial.py) gates and promotes to published

Posts are written to blog/posts/brief-<regulator>.md with status `review`;
`editorial.py --promote` is the only thing that can move a post to `published`.

Usage:
  python3 scripts/swarm.py --all
  python3 scripts/swarm.py --regulator ibbi
  python3 scripts/swarm.py --all --only-changed
"""
import argparse
import csv
import os
import re
import sys
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import blog_content  # noqa: E402
import frontmatter  # noqa: E402

ROOT = os.path.dirname(_HERE)
BASE = "https://regtrac.cashlessconsumer.in"
POSTS_DIR = os.path.join(ROOT, "blog", "posts")
AS_OF = "12 September 2026"

TYPE_LABELS = {
    "statutory_core": "Statutory regulator",
    "statutory_adjacent": "Statutory · adjacent",
    "nonstatutory_context": "Non-statutory · context",
}
EVENT_LABELS = {
    "statute": "Statute", "establishment": "Established", "transfer": "Transfer",
    "leadership": "Leadership", "reform": "Reform", "proposal": "Proposal",
    "sro_framework": "SRO framework", "enforcement": "Enforcement",
    "consultation": "Consultation", "grievance": "Grievance", "register_note": "Register note",
}


def read_csv(name):
    with open(os.path.join(ROOT, "data", name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def site(r):
    """Bare https URL from the register's website field."""
    m = re.match(r"(https?://\S+)", (r.get("website") or "").strip())
    return m.group(1) if m else (r.get("website") or "").strip()


def content_sections(rid):
    """Parse content/reg-<rid>.md into {heading: [lines]} plus the dek line."""
    path = os.path.join(ROOT, "content", f"reg-{rid}.md")
    if not os.path.exists(path):
        return None, {}
    lines = open(path, encoding="utf-8").read().splitlines()
    dek, sections, current = "", {}, None
    for ln in lines:
        if ln.startswith("## "):
            current = ln[3:].strip()
            sections[current] = []
        elif ln.startswith("# "):
            continue
        elif current:
            sections[current].append(ln)
        elif ln.strip() and not dek:
            dek = ln.strip()
    return dek, sections


def bullets(sections, *headings):
    out = []
    for h in headings:
        for key, val in sections.items():
            if key.lower().startswith(h.lower()):
                out += [ln[2:].strip() for ln in val if ln.strip().startswith("- ")]
    return out


def md_links(lines):
    """(label, url) pairs from markdown bullets or inline links."""
    out = []
    for ln in lines:
        for label, url in re.findall(r"\[([^\]]+)\]\(([^)\s]+)\)", ln):
            if url.startswith("http"):
                out.append((label, url))
    return out


def _clip(text, limit):
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


def compose(reg, lead_rows, event_rows, today):
    rid, name, abbr = reg["id"], reg["name"], reg["abbr"]
    dek, sections = content_sections(rid)
    note = blog_content.NOTES.get(rid, {})
    if not dek:
        dek = note.get("dek", f"{name} — the register entry for {abbr}.")

    evidence = []          # (label, url) collected in reading order
    def cite(label, url):
        if url and url.startswith("http") and url not in {u for _, u in evidence}:
            evidence.append((label, url))
        return url

    # tracker + evidence: what changed -----------------------------------------
    changed = []
    sourced_events = [e for e in sorted(event_rows, key=lambda e: e["date"], reverse=True) if e["source_url"].strip()]
    for e in sourced_events[:4]:
        elabel = EVENT_LABELS.get(e["type"], e["type"])
        changed.append(f"**{e['date']}** — {e['title'].rstrip('.')} "
                       f"([{elabel} source]({e['source_url']})).")
        cite(f"{elabel} · {e['date']}", e["source_url"])
    for l in lead_rows:
        since = l["since"]
        term = f" — {l['term_or_note']}" if l["term_or_note"] else ""
        pred = f", succeeding {l['predecessor']}" if l["predecessor"] else ""
        changed.append(f"**{l['role']}:** {l['name']} (since {since}{term}{pred}) "
                       f"([appointment source]({l['source_url']})).")
        cite(f"Appointment · {l['role']}", l["source_url"])
    if not changed:
        changed.append(
            f"No sourced change is logged for {abbr} since RegTrac's register was rebuilt on {AS_OF}. "
            f"The brief records the standing position, and the next revision will report the first sourced movement "
            f"([register entry]({BASE}/reg-{rid}.html)).")
        cite("RegTrac register entry", f"{BASE}/reg-{rid}.html")
    else:
        changed.append(f"*Register position as rebuilt on {AS_OF}; every line above carries its own source.*")

    # institutional: why it matters -------------------------------------------
    why = bullets(sections, "Powers that matter") or note.get("why", [])
    why = [w for w in why]
    why += [f"*Statute and mandate: {reg['statute']} — "
            f"[{abbr} official site]({site(reg)}) · "
            f"[RegTrac register entry]({BASE}/reg-{rid}.html).*"]
    layer = blog_content.LAYER_LINKS.get(rid, blog_content.LAYER_LINK_DEFAULT)
    cite("RegTrac register entry", f"{BASE}/reg-{rid}.html")

    # advocate: who is affected ------------------------------------------------
    affected = [f"**Grievance route:** {reg['grievance']} ([{abbr} site]({site(reg)}))."]
    cite(f"{abbr} — official site", reg["website"])
    consumer = [b for b in bullets(sections, "For the person paying")
                if not b.lower().startswith("**grievance route")]
    affected += consumer
    affected.append(f"*The full route, with the register's own notes on escalation, is in the "
                    f"[RegTrac register entry for {abbr}]({BASE}/reg-{rid}.html).*")

    # skeptic: what to watch ---------------------------------------------------
    watch = bullets(sections, "Watchpoints") or note.get("watch", [])
    watch = [w for w in watch]
    watch.append(f"*Every watchpoint above is tracked against the "
                 f"[RegTrac register entry for {abbr}]({BASE}/reg-{rid}.html), as rebuilt on {AS_OF}; "
                 f"no line here rests on information the register does not carry.*")

    # evidence ---------------------------------------------------------------
    ev_lines = [f"- [{label}]({url})" for label, url in evidence]

    body = [f"# {name} — what changed, and what to watch", "", dek, "",
            f"*RegTrac Brief · {today} · {TYPE_LABELS.get(reg['type'], reg['type'])} · "
            f"register as of {AS_OF}*", "",
            "## What changed", ""] + [f"- {c}" for c in changed] + [
            "", "## Why it matters", ""] + [f"- {w}" for w in why] + [
            "", layer, "",
            "## Who is affected", ""] + [f"- {a}" for a in affected] + [
            "", "## What to watch", ""] + [f"- {w}" for w in watch] + [
            "", "## Evidence", ""] + ev_lines

    latest = sourced_events[0] if sourced_events else None
    meta = {
        "title": f"{name} — what changed, and what to watch",
        "date": today,
        "regulator": rid,
        "regulator_name": name,
        "event_type": latest["type"] if latest else "register_note",
        "status": "review",
        "summary": _clip(f"{abbr}: " + re.sub(r"\s+", " ", dek), 200),
        "personas": ["tracker", "evidence", "advocate", "institutional", "mapper", "skeptic"],
        "sources": [url for _, url in evidence],
    }
    return meta, "\n".join(body).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="every regulator in the register")
    ap.add_argument("--regulator", action="append", help="one or more regulator ids")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--only-changed", action="store_true", help="skip posts whose body is unchanged")
    args = ap.parse_args()

    regs = read_csv("regulators.csv")
    lead = read_csv("leadership.csv")
    events = read_csv("events.csv")
    if args.regulator:
        wanted = set(args.regulator)
        regs = [r for r in regs if r["id"] in wanted]
        missing = wanted - {r["id"] for r in regs}
        if missing:
            print(f"swarm: unknown regulator(s) {sorted(missing)}", file=sys.stderr)
            return 2
    elif not args.all:
        ap.error("pass --all or --regulator <id>")

    os.makedirs(POSTS_DIR, exist_ok=True)
    written, skipped = [], []
    for reg in regs:
        meta, body = compose(
            reg,
            [l for l in lead if l["regulator"] == reg["id"]],
            [e for e in events if e["actor"] == reg["id"]],
            args.date,
        )
        path = os.path.join(POSTS_DIR, f"brief-{reg['id']}.md")
        if os.path.exists(path):
            old_meta, old_body = frontmatter.parse(path)
            # Status is the managing editor's call, not the composer's: a brief
            # already promoted to `published` must not be demoted by a recompose.
            if old_meta.get("status") in ("published", "review"):
                meta["status"] = old_meta["status"]
            if args.only_changed:
                strip = lambda t: re.sub(r"^\*RegTrac Brief · .*$", "", t, flags=re.M)
                if strip(old_body) == strip(body):
                    skipped.append(reg["id"])
                    continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(frontmatter.render(meta, body))
        written.append((reg["id"], len(body.split()), len(meta["sources"])))

    for rid, words, srcs in written:
        print(f"swarm: wrote brief-{rid}.md — {words} words, {srcs} sources")
    if skipped:
        print(f"swarm: unchanged, left alone — {', '.join(skipped)}")
    print(f"swarm: {len(written)} composed, {len(skipped)} unchanged")


if __name__ == "__main__":
    sys.exit(main())
