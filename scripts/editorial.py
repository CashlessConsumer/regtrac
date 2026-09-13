#!/usr/bin/env python3
"""RegTrac editorial gate — the managing editor persona.

Reads blog/posts/*.md and runs the swarm's checks as hard gates:

  tracker        front matter complete, regulator in register, valid date
  structure      the five required sections, in order
  evidence       >=1 https source, every source cited in the body, no section
                 with figures but no link, no unattributed hedging
  advocate       "Who is affected" names a grievance route
  mapper         the layer link to SROTrac / LobbyWatch is present
  skeptic        "What to watch" carries at least two watchpoints, no loaded framing
  editor         promotion: `--promote` publishes a clean draft

Blocking rules: a PUBLISHED post with any error fails the build. A draft or
review post only fails with `--strict` (used on pull requests). `--coverage`
additionally requires every regulator in the register to have a published brief.

Usage:
  python3 scripts/editorial.py check
  python3 scripts/editorial.py check --strict --summary -
  python3 scripts/editorial.py check --promote --coverage
"""
import argparse
import csv
import os
import re
import sys
from datetime import date, datetime, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import frontmatter  # noqa: E402

ROOT = os.path.dirname(_HERE)
POSTS_DIR = os.path.join(ROOT, "blog", "posts")

REQUIRED_HEADINGS = ["What changed", "Why it matters", "Who is affected",
                     "What to watch", "Evidence"]
REQUIRED_PERSONAS = ["tracker", "institutional", "advocate", "skeptic", "mapper", "evidence"]
EVENT_TYPES = {"statute", "establishment", "transfer", "leadership", "reform",
               "proposal", "sro_framework", "enforcement", "consultation",
               "grievance", "register_note"}
STATUSES = {"draft", "review", "published"}
HEDGES = ["it is believed", "sources say", "reportedly", "allegedly", "unconfirmed", "rumour", "rumor"]
LOADED = ["blatant", "corrupt", "shameful", "scam", "disaster", "destroyed"]
GRIEVANCE = ["ombudsman", "grievance", "complaint", "escalat", "scores", "bima bharosa", "redress"]
MIN_WORDS = 120


def read_csv(name):
    with open(os.path.join(ROOT, "data", name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def split_sections(body):
    sections, current, order = {}, None, []
    for ln in body.splitlines():
        if ln.startswith("## "):
            current = ln[3:].strip()
            order.append(current)
            sections[current] = []
        elif current:
            sections[current].append(ln)
    return sections, order


def check_post(path, reg_ids):
    meta, body = frontmatter.parse(path)
    rid = meta.get("regulator", "")
    errs, warns = [], []

    # tracker -----------------------------------------------------------------
    for field in ("title", "date", "regulator", "event_type", "status", "summary"):
        if not str(meta.get(field, "")).strip():
            errs.append(f"tracker: front matter missing `{field}`")
    if rid and rid not in reg_ids:
        errs.append(f"tracker: regulator `{rid}` is not in data/regulators.csv")
    if meta.get("status") and meta["status"] not in STATUSES:
        errs.append(f"tracker: status `{meta['status']}` not in {sorted(STATUSES)}")
    if meta.get("event_type") and meta["event_type"] not in EVENT_TYPES:
        errs.append(f"tracker: event_type `{meta['event_type']}` not in the taxonomy")
    try:
        d = datetime.strptime(str(meta.get("date", "")), "%Y-%m-%d").date()
        if d > date.today() + timedelta(days=1):
            errs.append(f"tracker: date {d} is in the future")
    except ValueError:
        errs.append(f"tracker: date `{meta.get('date')}` is not YYYY-MM-DD")

    # structure ---------------------------------------------------------------
    sections, order = split_sections(body)
    missing = [h for h in REQUIRED_HEADINGS if h not in sections]
    if missing:
        errs.append(f"structure: missing section(s) {missing}")
    else:
        idx = [order.index(h) for h in REQUIRED_HEADINGS]
        if idx != sorted(idx):
            errs.append("structure: required sections are out of order")
        if order[:len(REQUIRED_HEADINGS)] != REQUIRED_HEADINGS:
            warns.append("structure: extra section before the required five")

    # evidence ----------------------------------------------------------------
    sources = meta.get("sources") or []
    if not isinstance(sources, list):
        sources = [sources]
    sources = [s for s in sources if str(s).strip()]
    if not sources:
        errs.append("evidence: no sources in front matter")
    for s in sources:
        if not str(s).startswith("https://"):
            errs.append(f"evidence: source is not https — {s}")
        elif str(s) not in body:
            errs.append(f"evidence: source not cited in the body — {s}")
    for h in REQUIRED_HEADINGS:
        text = "\n".join(sections.get(h, []))
        low = text.lower()
        if re.search(r"\d", text) and "http" not in text:
            errs.append(f"evidence: `{h}` carries figures but no source link in the section")
        for hedge in HEDGES:
            if hedge in low and "http" not in text:
                errs.append(f"evidence: unattributed hedge `{hedge}` in `{h}`")

    # advocate ---------------------------------------------------------------
    text = "\n".join(sections.get("Who is affected", []))
    if not text.strip():
        errs.append("advocate: `Who is affected` is empty")
    elif not any(k in text.lower() for k in GRIEVANCE):
        errs.append("advocate: `Who is affected` names no grievance or escalation route")

    # mapper ------------------------------------------------------------------
    if "srotrac" not in body.lower() and "lobbywatch" not in body.lower():
        errs.append("mapper: no layer link (SROTrac / LobbyWatch) in the body")

    # skeptic ----------------------------------------------------------------
    bullets = [ln for ln in sections.get("What to watch", []) if ln.strip().startswith("- ")]
    if len(bullets) < 2:
        errs.append(f"skeptic: `What to watch` has {len(bullets)} watchpoint(s), needs >=2")
    low = body.lower()
    hits = [p for p in LOADED if p in low]
    if hits:
        errs.append(f"skeptic: loaded framing {hits} — state the gap, not the adjective")

    # editor -----------------------------------------------------------------
    personas = meta.get("personas") or []
    if not isinstance(personas, list):
        personas = [personas]
    words = len(body.split())
    if meta.get("status") == "published":
        absent = [p for p in REQUIRED_PERSONAS if p not in personas]
        if absent:
            errs.append(f"editor: published without sign-off from {absent}")
        if words < MIN_WORDS:
            errs.append(f"editor: published at {words} words, needs >= {MIN_WORDS}")

    return {"meta": meta, "body": body, "errors": errs, "warnings": warns,
            "words": words, "sections": sections, "personas": personas}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["check"])
    ap.add_argument("--strict", action="store_true", help="drafts with errors also fail")
    ap.add_argument("--coverage", action="store_true", help="require a published brief per regulator")
    ap.add_argument("--promote", action="store_true", help="publish clean drafts (managing editor)")
    ap.add_argument("--regulator", help="limit to one regulator")
    ap.add_argument("--summary", help="write a markdown report here ('-' for stdout)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    regs = read_csv("regulators.csv")
    reg_ids = {r["id"] for r in regs}
    if not os.path.isdir(POSTS_DIR):
        print("editorial: no blog/posts directory")
        return 2

    posts = []
    for name in sorted(os.listdir(POSTS_DIR)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(POSTS_DIR, name)
        res = check_post(path, reg_ids)
        res["path"], res["slug"] = path, name[:-3]
        posts.append(res)

    if args.regulator:
        posts = [p for p in posts if p["meta"].get("regulator") == args.regulator]

    # managing editor: promote clean drafts -----------------------------------
    promoted = []
    for p in posts:
        if args.promote and p["meta"].get("status") in ("draft", "review") and not p["errors"]:
            meta = dict(p["meta"])
            meta["status"] = "published"
            signoffs = list(p["personas"])
            for persona in REQUIRED_PERSONAS + ["editor"]:
                if persona not in signoffs:
                    signoffs.append(persona)
            meta["personas"] = signoffs
            with open(p["path"], "w", encoding="utf-8") as f:
                f.write(frontmatter.render(meta, p["body"]))
            p["meta"], p["personas"] = meta, signoffs
            promoted.append(p["slug"])

    # coverage ---------------------------------------------------------------
    publish_by_reg = {}
    for p in posts:
        if p["meta"].get("status") == "published":
            publish_by_reg.setdefault(p["meta"].get("regulator"), []).append(p)
    coverage_fail = []
    if args.coverage:
        for r in regs:
            if not publish_by_reg.get(r["id"]):
                coverage_fail.append(r["id"])

    blocking, warned = [], []
    for p in posts:
        if p["meta"].get("status") == "published" and p["errors"]:
            blocking.append(p)
        elif p["errors"] and args.strict:
            blocking.append(p)
        elif p["errors"]:
            warned.append(p)

    # report ------------------------------------------------------------------
    lines = ["# RegTrac editorial gate", "",
             f"Posts: {len(posts)} · published: {sum(1 for p in posts if p['meta'].get('status') == 'published')} "
             f"· promoted this run: {len(promoted)} · blocking: {len(blocking)}", "",
             "| Regulator | Entity | Briefs | Published | Words | Gate |",
             "| --- | --- | --- | --- | --- | --- |"]
    by_reg = {}
    for p in posts:
        by_reg.setdefault(p["meta"].get("regulator", "?"), []).append(p)
    for r in regs:
        rp = by_reg.get(r["id"], [])
        pub = sum(1 for p in rp if p["meta"].get("status") == "published")
        words = sum(p["words"] for p in rp)
        if not rp:
            gate = "— no brief"
        elif any(p in blocking for p in rp):
            gate = "❌ FAIL"
        elif any(p["errors"] for p in rp):
            gate = "⚠ review"
        else:
            gate = "✅ pass"
        lines.append(f"| `{r['id']}` | {r['name']} | {len(rp)} | {pub} | {words} | {gate} |")
    if args.coverage:
        lines += ["", f"Coverage: {len(publish_by_reg)}/{len(regs)} regulators with a published brief"
                  + (f" — missing {coverage_fail}" if coverage_fail else "")]
    for p in posts:
        if not p["errors"] and not p["warnings"]:
            continue
        lines += ["", f"### {p['slug']} ({p['meta'].get('status')})",
                  f"- regulator: `{p['meta'].get('regulator')}` · {p['words']} words"]
        lines += [f"- {'ERROR' if e in [x for x in p['errors']] else 'warn'}: {e}" for e in p["errors"]]
        lines += [f"- warn: {w}" for w in p["warnings"]]

    report = "\n".join(lines)
    if args.summary == "-":
        print(report)
    elif args.summary:
        with open(args.summary, "w", encoding="utf-8") as f:
            f.write(report + "\n")
    if not args.quiet and args.summary != "-":
        print(report)

    if blocking or coverage_fail:
        if not args.quiet:
            print(f"\neditorial: BLOCKED — {len(blocking)} post(s) with errors"
                  + (f", coverage gaps {coverage_fail}" if coverage_fail else ""), file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"\neditorial: PASS — {len(posts)} post(s) gated"
              + (f", {len(warned)} draft(s) warned" if warned else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
