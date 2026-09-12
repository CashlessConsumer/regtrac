# RegTrac

**The watchers, watched.** A public register of India's statutory financial regulators — their statutes, powers, leadership appointments, grievance machinery and accountability gaps.

**Live:** https://regtrac.cashlessconsumer.in (GitHub Pages; falls back to https://cashlessconsumer.github.io/regtrac/ until the DNS CNAME `regtrac → cashlessconsumer.github.io` is added on Netlify DNS)

Part of a three-layer **sousveillance stack** for financial-sector policy making in India:

| Layer | Project | Status | Tracks |
| --- | --- | --- | --- |
| Rule-writers | **RegTrac** (this) | live | statutory regulators |
| Rule-borrowers | [SROTrac](https://srotrac.cashlessconsumer.in) | live | RBI-recognised SROs + rosters |
| Rule-buyers | LobbyWatch | planned | consultations, access, revolving doors |

Concept and build order for the third layer: `SOUSVEILLANCE.md`.

## Register (as of 2026-09-12)

- **Statutory core (7):** RBI, SEBI, IRDAI, PFRDA, IBBI, IFSCA, NABARD
- **Statutory adjacent (4):** DICGC, NHB, SIDBI, NFRA
- **Non-statutory context (2, flagged):** FSDC, NPCI

13 entities · 14 sourced appointments · 38 timeline events.

## Layout

```
data/regulators.csv    register: statute, ministry, mandate, grievance, status
data/leadership.csv    appointments: role, name, since, predecessor, source_url
data/events.csv        timeline: statutes, reforms, leadership changes (sourced)
data/regtrac.duckdb    queryable copy (regulators, leadership, events)
scripts/build.py       CSVs → all HTML + duckdb + llms.txt + sitemap + og.png
css/style.css          hand-written (not generated)
SOUSVEILLANCE.md       the stack concept + LobbyWatch build order
AGENTS.md              agent conventions (scope, sourcing, build/deploy)
```

## Build & deploy

```bash
python3 scripts/build.py   # regenerate everything from data/
git push                   # main → GitHub Actions → Pages (~25s)
```

Never hand-edit generated HTML. Update `data/*.csv` (and the per-entity content dicts in `scripts/build.py` for deep pages), rebuild, push.

## Query the data

```bash
duckdb data/regtrac.duckdb -c "SELECT * FROM leadership ORDER BY since DESC"
duckdb data/regtrac.duckdb -c "SELECT * FROM events WHERE type='statute'"
```

---
CashlessConsumer · consumer collective for digital payments & fintech · *surveillance is watching citizens; sousveillance is citizens watching back.*
