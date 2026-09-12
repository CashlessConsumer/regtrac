# RegTrac — agent conventions

Layer 1 (rule-writers) of the sousveillance stack: RegTrac (this) + SROTrac (`Projects/srotrac/`) + LobbyWatch (planned). Read `SOUSVEILLANCE.md` for the concept; keep layer language consistent across all three ("rule-writers / rule-borrowers / rule-buyers").

## Scope rules

- **RegTrac = statutory regulators of India's financial sector** (central statutes). SROs and industry associations belong to SROTrac. Consultation-commentary/lobby access belongs to LobbyWatch (not built). If an item fits two layers, RegTrac holds the regulator-side fact and cross-links ("layer link") to the other project — do not duplicate rosters here.
- **Statutory core** (7): RBI, SEBI, IRDAI, PFRDA, IBBI, IFSCA, NABARD. **Statutory adjacent**: DICGC, NHB, SIDBI, NFRA. **Non-statutory context** (clearly flagged): FSDC, NPCI. Adding entities requires a central statute — no ministries, no associations.
- Leadership rows **must** carry a source_url (PIB, RBI/SEBI/IRDAI press releases, or mainstream business press). ETBFSI 2025 recap + regulator sites are acceptable; unverified WhatsApp-forward-style aggregators are not.
- Current leadership facts (as of 2026-09-12): RBI Gov Sanjay Malhotra (Dec 2024); DGs Rabi Sankar, Janakiraman (reappointed to Jun 2028), Poonam Gupta (Apr 2025), Murmu (Oct 2025); SEBI Tuhin Kanta Pandey (Feb/Mar 2025); IRDAI Ajay Seth (term from ~Sep 2025; predecessor Debasish Panda); PFRDA S. Ramann (Jun 2025); IFSCA K. Rajaraman (extended to Oct 2028); IBBI Ravi Mital (succession search opened Jun 2026); NABARD Shaji K V (since 2023). IBBI succession and any PFRDA/SEBI WTM churn are the most likely near-term changes — re-verify before editing.

## Build & deploy

- Single source of truth: `data/*.csv` → `python3 scripts/build.py` regenerates all HTML + `data/regtrac.duckdb` + llms.txt/llms-full.txt + sitemap + robots + og.png. Never hand-edit generated HTML.
- Deploy = push to `main` (GitHub Actions → Pages, workflow build type). Live: https://regtrac.cashlessconsumer.in (CNAME file already in repo; **DNS CNAME record `regtrac → cashlessconsumer.github.io` still needs manual add on Netlify DNS** — token cannot write DNS records).
- duckdb ≥1.4 requires explicit column types in CREATE TABLE — build.py already emits `VARCHAR`; keep that pattern.
- Per-rule: always pass explicit absolute output paths to any CLI that writes files (agent-browser screenshot takes `--full`, not `--full-page`).

## Content voice

- Consumer-first ("For the person paying" section on every entity page — grievance routes with escalation steps).
- Watchpoints name the accountability gap in plain language (ACC appointments, unpublished consultation comments, Calcutta HC ruling on IBBI Chairperson acting as Disciplinary Committee, etc.).
- Every number sourced; if a figure is unsourced, leave it out.
