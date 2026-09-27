# RegTrac — agent conventions

Layer 1 (rule-writers) of the sousveillance stack: RegTrac (this) + SROTrac (`Projects/srotrac/`) + LobbyWatch (live 2026-09-26, `Projects/lobbywatch/`, lobbywatch.cashlessconsumer.in). Read `SOUSVEILLANCE.md` for the concept; keep layer language consistent across all three ("rule-writers / rule-borrowers / rule-buyers").

## Scope rules

- **RegTrac = statutory regulators of India's financial sector** (central statutes). SROs and industry associations belong to SROTrac. Consultation-commentary/lobby access belongs to LobbyWatch (live since 2026-09-26). If an item fits two layers, RegTrac holds the regulator-side fact and cross-links ("layer link") to the other project — do not duplicate rosters here.
- **Statutory core** (7): RBI, SEBI, IRDAI, PFRDA, IBBI, IFSCA, NABARD. **Statutory adjacent**: DICGC, NHB, SIDBI, NFRA. **Non-statutory context** (clearly flagged): FSDC, NPCI. Adding entities requires a central statute — no ministries, no associations.
- Leadership rows **must** carry a source_url (PIB, RBI/SEBI/IRDAI press releases, or mainstream business press). ETBFSI 2025 recap + regulator sites are acceptable; unverified WhatsApp-forward-style aggregators are not.
- Current leadership facts (as of 2026-09-12): RBI Gov Sanjay Malhotra (Dec 2024); DGs Rabi Sankar, Janakiraman (reappointed to Jun 2028), Poonam Gupta (Apr 2025), Murmu (Oct 2025); SEBI Tuhin Kanta Pandey (Feb/Mar 2025); IRDAI Ajay Seth (term from ~Sep 2025; predecessor Debasish Panda); PFRDA S. Ramann (Jun 2025); IFSCA K. Rajaraman (extended to Oct 2028); IBBI Ravi Mital (succession search opened Jun 2026); NABARD Shaji K V (since 2023). IBBI succession and any PFRDA/SEBI WTM churn are the most likely near-term changes — re-verify before editing.

## Build & deploy

- Single source of truth: `data/*.csv` → `python3 scripts/build.py` regenerates all HTML + `data/regtrac.duckdb` + llms.txt/llms-full.txt + sitemap + robots + og.png. Never hand-edit generated HTML.
- Deploy = push to `main` (GitHub Actions → Pages, workflow build type). Live: https://regtrac.cashlessconsumer.in (CNAME file already in repo; **DNS CNAME record `regtrac → cashlessconsumer.github.io` still needs manual add on Netlify DNS** — token cannot write DNS records).
- duckdb ≥1.4 requires explicit column types in CREATE TABLE — build.py already emits `VARCHAR`; keep that pattern.
- Per-rule: always pass explicit absolute output paths to any CLI that writes files (agent-browser screenshot takes `--full`, not `--full-page`).

## Blog / weekly edition

Nav label is **Blog** (synced with SROTrac; the old "Briefs" label is retired). `scripts/bloggen.py` renders every `blog/posts/*.md` into `blog/` — per-regulator briefs carry `regulator: <id>`, weekly editions (`event_type: weekly`) omit it and surface on the index + feed only. The **RegTrac Weekly agent** (Zo automation, Mondays 09:20 IST, posts to Discord #policy-research) researches the week's most consequential development across the register, writes a sourced post, rebuilds, tests (test_publication.py must ALL PASS), and pushes. Inaugural post: `2026-09-26-ibbi-succession-watch.md`.

## Content voice

- Consumer-first ("For the person paying" section on every entity page — grievance routes with escalation steps).
- Watchpoints name the accountability gap in plain language (ACC appointments, unpublished consultation comments, Calcutta HC ruling on IBBI Chairperson acting as Disciplinary Committee, etc.).
- Every number sourced; if a figure is unsourced, leave it out.

## Editorial pipeline (persona swarm → gate → publication test)

Three scripts, one direction: the swarm proposes, the managing editor disposes, the test proves the result shipped.

| Stage | Command | Output |
| --- | --- | --- |
| compose | `python3 scripts/swarm.py --all [--only-changed]` | `blog/posts/brief-<id>.md`, one per regulator, `status: review`, six personas credited |
| gate | `python3 scripts/editorial.py check [--strict] [--coverage] [--promote] [--summary FILE]` | pass/fail per post + a markdown report; `--promote` flips clean drafts to `published` |
| render | `python3 scripts/build.py && python3 scripts/bloggen.py` | blog pages, per-regulator streams, `feed.xml`, sitemap, duckdb |
| test (offline) | `python3 tests/test_publication.py [--regulator ID] [--markdown FILE]` | per-regulator matrix: brief reachable from entity page, own stream, cross-regulator stream, sitemap, feed |
| test (live) | `python3 tests/test_live.py [--base URL]... [--fallback]` | same matrix over HTTP against the deployed site |

- Supporting modules: `frontmatter.py` (front-matter reader/writer), `blog_content.py` (editorial-desk notes for entities with no deep-dive page, plus layer links).
- Composer never sets editorial status: an existing `published`/`review` status is preserved on recompose, so a `swarm.py --all` run cannot silently demote a brief out of `feed.xml`.
- `tests/test_live.py` defaults to the custom domain and offers `--fallback` to `https://cashlessconsumer.github.io/regtrac` — the custom-domain CNAME is still pending, so use `--base https://cashlessconsumer.github.io/regtrac` in CI.
- Personas credited per brief: tracker · evidence · advocate · institutional · mapper · skeptic · editor. The editor is `scripts/editorial.py`.
- Gate rules: every `What changed` / `Who is affected` / `What to watch` bullet that carries a figure needs a source link in that section; sources declared in front matter must survive into the rendered page; no bare `Rs`/`crore`/`per cent` without attribution.
- `--coverage` requires a published brief for every regulator in `data/regulators.csv`; `--strict` makes drafts with errors block the run. Use both in CI, plus `--promote` only on `main`.
- **CI ownership:** `editorial.yml` owns compose + gate + test, and on `main` it commits promoted artifacts but never deploys. `deploy.yml` owns the `pages-*` concurrency group and is the single publisher. Never give the two workflows the same concurrency group — that made them cancel each other on every push.
- On `main`, the editorial job commits promoted artifacts and then **dispatches `deploy.yml` explicitly** — a push made with the default `GITHUB_TOKEN` does not trigger other workflows, so a bot commit alone would leave the promoted briefs unpublished.
- CI entry points: `editorial.yml` (PR gate + one sticky PR comment, `main` publish, `workflow_dispatch` with an optional `regulator` input) and `deploy.yml` (build + Pages, `workflow_dispatch` enabled). Both exercised green on 2026-09-13.
- `deploy.yml` ends with a non-blocking `smoke` job (`tests/test_live.py`) that fetches every regulator's entity page, stream and briefs over HTTP from https://cashlessconsumer.github.io/regtrac after a 30 s propagation wait. Point it anywhere with `python3 tests/test_live.py --base <url>`; the branded domain is skipped until its DNS CNAME lands.

## Design language (decision 2026-09-26, synchronised)

One shared design language for the sousveillance stack: the SROTrac gazette/ledger skin (paper #ededf0, ruled lines + grain, seal blue #1d4ed8, Fraunces/Newsreader/IBM Plex Mono, ledger tables, stack band + gazette footer on every page). This supersedes the earlier separate-skins decision — the user called for synchronised UI/UX. RegTrac was ported from the old dark navy/amber brief to the gazette language on 2026-09-26; SROTrac is the reference implementation (its `scripts/site.py` CSS + masthead/footer/band are the source of truth).

Shared contract: `.stack` band markup identical on both (same classes, "You are here" on the live layer); same masthead anatomy (brand em + mono uppercase nav); same 4-paragraph site-footer. Site-specific content components (regulator tables, leadership grids, briefs stream) keep RegTrac's classes but are styled from SROTrac's patterns — when SROTrac's design moves, port it here.

## Activity & Social pages (2026-09-26, SROTrac parity)

- `activity.html` — newest-first feed: 14 leadership appointments (from `leadership.csv`) + all 38 tracked events (`events.csv`), per-type `fchip` filters. Distinct from Timeline (chronological history ledger).
- `social.html` — official-accounts register: 40 accounts across 13 entities in `data/social.csv` (columns: entity,platform,handle,url,source,verified,notes). `source=official site` rows carry the ✓ drift check; `source=platform lookup` rows (SEBI x2, IRDAI x2, NABARD x4) carry the ✎ mark and are skipped by the checker. FSDC has no public accounts (coordination council). Per-entity strips render on every `reg-*.html` page.
- Drift check: `python3 scripts/social_check.py` verifies each official-site account is still linked from the entity's own homepage snapshot in `data/raw/*.html` (site→account direction; platform walls can't block this). Writes `data/social_check.json`. Missing handles = ⚠ rebrand/takeover early signal.
- Pipeline: `scripts/refresh.sh` = homepage re-fetch → build.py → bloggen.py → social_check.py → commit/push on change (rebases before push; CI deploys). Runs daily 07:45 IST via automation (posts one line to Discord #policy-research, silent unless changed/drift).
- NPCI (Akamai) and NABARD block curl: refresh logs FETCH FAIL (stale snapshot, non-fatal). Re-capture `data/raw/npci.html` via agent-browser when its accounts look stale.

2026-09-26 pipeline parity: RegTrac now mirrors SROTrac's content pipeline — activity.html (reverse-chron feed), social.html (official-accounts register with per-entity cards + drift check via scripts/social_check.py against data/raw/ snapshots), scripts/refresh.sh daily (07:45 IST automation, #policy-research). When a shared pipeline component moves, land it in both repos same-day.

## Blog archive layer (2026-09-27)

`scripts/bloggen.py` now also renders `blog/archive.html` (all posts grouped year → month with event_type chips + filter) and `blog/<year>.html` per year; `blog/index.html` is capped to the latest 12 with year navigation, and archive/year URLs are patched into `sitemap.xml`. Categories on this desk = the posts' `event_type` (weekly/leadership/reform/…). The weekly agent (`500c6e1b`) is instructed to write the annual review edition ("The year in regulation <YYYY>") on the first Monday of January.
