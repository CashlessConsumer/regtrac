#!/usr/bin/env python3
"""RegTrac per-regulator publication test.

Run after `build.py` + `bloggen.py`. Asserts that every brief the editorial gate
published is actually reachable, per regulator, through every surface the site
offers — and that generated pages carry no unrendered template or markdown.

  python3 tests/test_publication.py
  python3 tests/test_publication.py --regulator rbi
  python3 tests/test_publication.py --markdown report.md   # also write the matrix
"""
import argparse
import csv
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import frontmatter  # noqa: E402

POSTS_DIR = os.path.join(ROOT, "blog", "posts")
BLOG_DIR = os.path.join(ROOT, "blog")
BASE = "https://regtrac.cashlessconsumer.in"

# Markers that mean generation went wrong rather than content being interesting.
BAD_MARKERS = ["{items}", "{link}", "{rows}", "{body_md}", "None</", "](http", "{{"]
UNRENDERED = re.compile(r"\{[a-z_]+\}")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regulator", action="append", help="limit the check to one or more ids")
    ap.add_argument("--markdown", help="write the matrix report to this path")
    args = ap.parse_args()

    with open(os.path.join(ROOT, "data", "regulators.csv"), newline="", encoding="utf-8") as f:
        regs = list(csv.DictReader(f))
    if args.regulator:
        regs = [r for r in regs if r["id"] in set(args.regulator)]

    posts = []
    if os.path.isdir(POSTS_DIR):
        for name in sorted(os.listdir(POSTS_DIR)):
            if name.endswith(".md"):
                meta, _ = frontmatter.parse(os.path.join(POSTS_DIR, name))
                posts.append({"slug": name[:-3], "meta": meta,
                              "regulator": str(meta.get("regulator", "")),
                              "status": str(meta.get("status", "draft"))})
    live = [p for p in posts if p["status"] in ("published", "review")]

    blog_index = read(os.path.join(BLOG_DIR, "index.html"))
    feed = read(os.path.join(BLOG_DIR, "feed.xml"))
    sitemap = read(os.path.join(ROOT, "sitemap.xml"))

    failures, rows = [], []
    for r in regs:
        rid, abbr = r["id"], r["abbr"]
        mine = [p for p in live if p["regulator"] == rid]
        problems = []

        stream_path = os.path.join(BLOG_DIR, f"reg-{rid}.html")
        if not os.path.exists(stream_path):
            problems.append("no per-regulator stream page")
            stream = ""
        else:
            stream = read(stream_path)

        # entity page must link to the stream
        ent_path = os.path.join(ROOT, f"reg-{rid}.html")
        if os.path.exists(ent_path):
            ent = read(ent_path)
            if f"blog/reg-{rid}.html" not in ent:
                problems.append("entity page does not link to its briefs stream")
            if 'href="blog/index.html"' not in ent:
                problems.append("entity page nav has no Briefs link")
        else:
            problems.append("entity page missing")

        for p in mine:
            slug = p["slug"]
            title = str(p["meta"].get("title", slug))
            page_path = os.path.join(BLOG_DIR, f"{slug}.html")
            if not os.path.exists(page_path):
                problems.append(f"{slug}: post page not rendered")
                continue
            body = read(page_path)
            if title not in body:
                problems.append(f"{slug}: post page missing its title")
            for marker in BAD_MARKERS:
                if marker in body:
                    problems.append(f"{slug}: unrendered marker {marker!r}")
            if UNRENDERED.search(body):
                problems.append(f"{slug}: unrendered placeholder in output")
            url = f"{BASE}/blog/{slug}.html"
            if url not in sitemap:
                problems.append(f"{slug}: absent from sitemap.xml")
            if url not in feed:
                problems.append(f"{slug}: absent from feed.xml")
            # Links are relative per surface: blog/index.html and blog/reg-<id>.html
            # sit inside blog/, while the entity page sits at the site root.
            if f'href="{slug}.html"' not in blog_index:
                problems.append(f"{slug}: absent from the cross-regulator stream")
            if f'href="{slug}.html"' not in stream:
                problems.append(f"{slug}: absent from its regulator stream")
            if f'href="blog/{slug}.html"' not in ent:
                problems.append(f"{slug}: entity page does not link the brief")
            # every source in the front matter must survive into the page
            srcs = p["meta"].get("sources") or []
            if not isinstance(srcs, list):
                srcs = [srcs]
            for s in srcs:
                if s and s not in body:
                    problems.append(f"{slug}: source dropped from page — {s}")

        # every stream must render its own nav + footer, at the right depth
        if stream:
            for needle in ("../index.html", "../css/style.css", "RegTrac Briefs" if False else "RegTrac"):
                if needle not in stream:
                    problems.append(f"stream missing {needle!r}")
            if 'href="/blog/' in stream:
                problems.append("stream uses root-absolute links (breaks on the Pages sub-path)")

        status = "PASS" if not problems else "FAIL"
        rows.append((rid, abbr, len(mine), status, problems))
        failures += [(rid, p) for p in problems]

    width = max(len(r[1]) for r in rows) if rows else 10
    out = [f"# RegTrac publication test — {len(rows)} regulators, {len(live)} briefs", ""]
    out.append(f"| {'id':<8} | {'entity':<{width}} | briefs | result |")
    out.append(f"| {'-'*8} | {'-'*width} | ------ | ------ |")
    for rid, abbr, n, status, _ in rows:
        out.append(f"| {rid:<8} | {abbr:<{width}} | {n:>6} | {status} |")
    if failures:
        out.append("")
        out.append("Failures:")
        for rid, p in failures:
            out.append(f"  [{rid}] {p}")
    published = sum(1 for r in rows if r[2])
    out.append("")
    out.append(f"{published}/{len(rows)} regulators with a rendered brief · "
               f"{'ALL PASS' if not failures else f'{len(failures)} FAILURE(S)'}")

    report = "\n".join(out)
    print(report)
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(report + "\n")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
