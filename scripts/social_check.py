#!/usr/bin/env python3
"""Social-presence drift check for RegTrac.

For every account in data/social.csv whose source is 'official site',
verify the account still appears in the latest raw homepage snapshots
under data/raw/. Writes data/social_check.json; build.py renders the
result on social.html.

Platform walls (X, LinkedIn, Facebook, Instagram) block automated fetches,
so this checks the *other* direction: does the regulator's own website
still link the account? An account removed from the official site is the
cheapest early signal of a rebrand, a takeover, or an account quietly
deleted. NABARD and NPCI block plain fetches (WAF), so their rows are
'platform lookup' or browser-verified and simply fall outside this check.

Usage: python3 scripts/social_check.py
"""
import csv
import glob
import html as htmllib
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load_raw_text():
    """Concatenate all raw homepage snapshots, unescaping entities and scheme."""
    chunks = []
    for path in sorted(glob.glob(os.path.join(DATA, "raw", "*.html"))):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                chunks.append(f.read())
        except OSError:
            continue
    text = "\n".join(chunks)
    text = htmllib.unescape(text)
    text = re.sub(r"https?://(www\.)?", "", text)
    return text.lower()


def probe_for(url):
    """Candidate substrings; twitter.com and x.com are equivalent."""
    p = re.sub(r"^https?://(www\.)?", "", url.strip()).rstrip("/").lower()
    cands = [p]
    if p.startswith("x.com/"):
        cands.append("twitter.com/" + p[6:])
    elif p.startswith("twitter.com/"):
        cands.append("x.com/" + p[12:])
    if p.startswith("youtube.com/channel/"):
        cands.append(p.rsplit("/", 1)[-1])
    return cands


def main():
    with open(os.path.join(DATA, "social.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    corpus = load_raw_text()

    official = [r for r in rows if r["source"].strip() == "official site"]
    checked, present, missing = 0, 0, []
    for r in official:
        checked += 1
        if any(c in corpus for c in probe_for(r["url"])):
            present += 1
        else:
            missing.append(f'{r["entity"]}:{r["platform"]}')

    result = {
        "checked": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "official_site_accounts": checked,
        "still_linked": present,
        "missing_from_site": missing,
        "skipped_platform_lookup": len(rows) - checked,
    }
    with open(os.path.join(DATA, "social_check.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"social check: {present}/{checked} official-site links still live; "
          f"missing={missing or 'none'}; skipped (platform lookup)={result['skipped_platform_lookup']}")


if __name__ == "__main__":
    main()
