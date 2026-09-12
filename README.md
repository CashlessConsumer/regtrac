# RegTrac — the watchers, watched

Public register of India's **statutory financial regulators**: their statutes, powers,
leadership appointments, grievance machinery and accountability gaps.

**Live**: https://regtrac.cashlessconsumer.in (GitHub Pages, repo `CashlessConsumer/regtrac`)
Raw fallback: https://cashlessconsumer.github.io/regtrac/

By [CashlessConsumer](https://cashlessconsumer.in) · a sousveillance project.
*Surveillance is watching citizens; sousveillance is citizens watching back.*

## The sousveillance stack

| Layer | Project | Tracks | Status |
| --- | --- | --- | --- |
| Rule-writers | **RegTrac** (this repo) | Statutory regulators of the financial sector | live |
| Rule-borrowers | [SROTrac](https://srotrac.cashlessconsumer.in) | RBI/SEBI-recognised SROs, their rosters and members | live |
| Rule-buyers | **LobbyWatch** | Consultations: who commented, access, revolving doors | planned |

See `SOUSVEILLANCE.md` for the three-layer concept and what LobbyWatch must cover.

## Register (v1)

**Statutory core** — RBI, SEBI, IRDAI, PFRDA, IBBI, IFSCA, NABARD
**Statutory adjacent** — DICGC (deposit insurance), NHB (housing, post-2019), SIDBI (development finance), NFRA (audit oversight)
**Non-statutory context** — FSDC (executive apex council), NPCI (Section 8, The Clearing Corporation of India context)

Each entity page: statute & setup · what it regulates · powers that matter ·
leadership table (sourced per row, "as of" stamped) · for the person paying
(grievance routes) · watchpoints (capture & accountability) · layer links to SROTrac.

## Repo layout

```
data/regulators.csv    register: id, statute, established, ministry, mandate, website, grievance, status
data/leadership.csv    appointments: role, name, since, term_or_note, predecessor, appointing_authority, source_url
data/events.csv        timeline: date, actor, type (statute/reform/leadership/proposal/SRO framework), title, source_url
scripts/build.py       builds all HTML + data/regtrac.duckdb + llms.txt/llms-full.txt + sitemap.xml + robots.txt + og.png
css/style.css          single stylesheet (dark, serif display)
.github/workflows/     Build & Deploy → GitHub Pages (workflow build type)
CNAME                  regtrac.cashlessconsumer.in
```

## Build

```bash
python3 scripts/build.py   # regenerates every page + duckdb + static files
```

Edit the CSVs, run build, commit, push. Deploy is push-to-main via Actions.
No JS framework; plain static HTML, ~17 pages.

## Data

- `data/regtrac.duckdb` — tables: `regulators`, `leadership`, `events` (all VARCHAR).
- `llms.txt` / `llms-full.txt` — machine-readable summaries for LLM consumers.

## Ground rules

1. **Source every leadership row** — one URL per appointment, no exceptions.
2. **"As of" stamped** — leadership positions carry an as-of date in the build; stale rows are corrected, not silently overwritten.
3. **Statutory vs non-statutory is flagged** — FSDC/NPCI are context, clearly labelled.
4. **Consumer section mandatory** — every entity page answers "what does this mean for the person paying".
5. **Capture watchpoints in plain language** — who appoints, who sits on boards, what is not published.

## Status / next

- [x] v1 register, leadership (14 appointments, as of 2026-09-12), 38-event timeline, live
- [ ] DNS: CNAME record `regtrac → cashlessconsumer.github.io` on Netlify DNS (manual; token cannot write DNS)
- [ ] Per-regulator board composition (full member lists, not just chair)
- [ ] Consultation-papers watcher per regulator (feeds future LobbyWatch)
- [ ] Weekly automation: leadership-change scan + timeline additions
