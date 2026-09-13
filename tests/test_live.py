#!/usr/bin/env python3
"""RegTrac live per-regulator publication check, over HTTP.

Sibling of `test_publication.py`: that one asserts the generated files on disk,
this one asserts the deployed site actually serves them. For every regulator in
`data/regulators.csv`:

  - the entity page renders and links its briefs stream
  - the per-regulator stream renders its chrome
  - every brief for that regulator renders, carries its title, and keeps every
    source URL from its front matter

Defaults to the GitHub Pages URL, which is where the site is actually served
today. The branded domain (https://regtrac.cashlessconsumer.in) is not live yet
— its Netlify DNS CNAME is still pending — so check it explicitly once it lands:

  python3 tests/test_live.py
  python3 tests/test_live.py --base https://regtrac.cashlessconsumer.in
  python3 tests/test_live.py --base https://regtrac.cashlessconsumer.in --base https://cashlessconsumer.github.io/regtrac
"""
import argparse
import csv
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import frontmatter  # noqa: E402

DEFAULT_BASE = "https://cashlessconsumer.github.io/regtrac"
BRANDED_BASE = "https://regtrac.cashlessconsumer.in"


def get(url, retries=3):
    """Return (status, body). Retries transient CDN/network errors."""
    last = (0, "")
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": "regtrac-live-check"})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = (e.code, "")
            if e.code < 500:
                return last
        except Exception as e:  # noqa: BLE001 — report, don't crash the matrix
            last = (0, str(e))
        if attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
    return last


def load_posts():
    posts = {}
    d = os.path.join(ROOT, "blog", "posts")
    if not os.path.isdir(d):
        return posts
    for name in sorted(os.listdir(d)):
        if name.endswith(".md"):
            meta, _ = frontmatter.parse(os.path.join(d, name))
            posts[name[:-3]] = meta
    return posts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", action="append",
                    help=f"site base URL (default {DEFAULT_BASE})")
    ap.add_argument("--branded", action="store_true",
                    help=f"also check the branded domain {BRANDED_BASE} (DNS pending)")
    args = ap.parse_args()

    with open(os.path.join(ROOT, "data", "regulators.csv"), newline="", encoding="utf-8") as f:
        regs = list(csv.DictReader(f))
    posts = load_posts()

    bases = args.base or [DEFAULT_BASE]
    if args.branded and BRANDED_BASE not in bases:
        bases.append(BRANDED_BASE)

    failures = []
    for base in bases:
        print(f"\n## {base}\n")
        print("| id | entity page | stream | briefs | result |")
        print("| --- | --- | --- | --- | --- |")

        jobs = []
        for r in regs:
            rid = r["id"]
            jobs.append((rid, f"{base}/reg-{rid}.html", "ent"))
            jobs.append((rid, f"{base}/blog/reg-{rid}.html", "stream"))
            for slug, meta in posts.items():
                if str(meta.get("regulator")) == rid:
                    jobs.append((rid, f"{base}/blog/{slug}.html", slug))

        with ThreadPoolExecutor(max_workers=12) as ex:
            results = list(ex.map(lambda j: (j, *get(j[1])), jobs))

        by = {}
        for (rid, url, kind), status, body in results:
            by.setdefault(rid, []).append((kind, url, status, body))
            if status != 200:
                failures.append(f"[{base}] [{rid}] {kind} {url} -> HTTP {status}")
            elif kind == "ent":
                if f"blog/reg-{rid}.html" not in body:
                    failures.append(f"[{base}] [{rid}] entity page does not link its stream")
            elif kind == "stream":
                if "RegTrac" not in body:
                    failures.append(f"[{base}] [{rid}] stream missing chrome")
            else:
                if str(posts[kind].get("title", kind)) not in body:
                    failures.append(f"[{base}] [{rid}] {kind}: missing title")
                for s in (posts[kind].get("sources") or []):
                    if s and s not in body:
                        failures.append(f"[{base}] [{rid}] {kind}: source dropped — {s}")

        for r in regs:
            rid = r["id"]
            rows = by.get(rid, [])
            briefs = [x for x in rows if x[0] not in ("ent", "stream")]
            ok = all(x[2] == 200 for x in rows)
            ent_ok = any(x[0] == "ent" and x[2] == 200 for x in rows)
            st_ok = any(x[0] == "stream" and x[2] == 200 for x in rows)
            print(f"| {rid} | {'ok' if ent_ok else 'FAIL'} | {'ok' if st_ok else 'FAIL'} | "
                  f"{len(briefs)} | {'PASS' if ok and briefs else 'FAIL'} |")

    print()
    if failures:
        print(f"{len(failures)} LIVE FAILURE(S):")
        for f_ in failures:
            print("  " + f_)
        return 1
    print("LIVE: all regulators, streams and briefs rendered — ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
