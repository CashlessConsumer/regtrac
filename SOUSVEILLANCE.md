# The Sousveillance Stack — India's financial policy machine, watched back

*Surveillance is watching citizens; **sousveillance** is citizens watching back.*

India's financial sector policy is made in three rooms. Each room now has a watcher.

```
┌────────────────────────────────────────────────────────────────────┐
│ Room 1: Rule-WRITERS  →  RegTrac        (live, this repo)          │
│   Statutory regulators: RBI, SEBI, IRDAI, PFRDA, IBBI, IFSCA…     │
│   Watched: statutes, powers, appointments, grievance machinery,   │
│   accountability gaps. Who gets the job, from whom, for how long. │
├────────────────────────────────────────────────────────────────────┤
│ Room 2: Rule-BORROWERS  →  SROTrac      (live)                     │
│   srotrac.cashlessconsumer.in                                     │
│   Regulators delegate rule-borrowing to recognised SROs:          │
│   FACE, UFF (fintech), FIDC, MFIN, Sa-Dhan, SRPA, FEDAI,          │
│   Sahamati. Watched: rosters, who the members are, governance.    │
├────────────────────────────────────────────────────────────────────┤
│ Room 3: Rule-BUYERS  →  LobbyWatch      (planned)                  │
│   Watched (to build):                                             │
│   • Consultation papers — who commented, and did the final rule   │
│     move toward the comments? (Regulators publish comments        │
│     inconsistently; RBI publishes almost none.)                   │
│   • Access — RTI for meeting minutes: who met the regulator,      │
│     when, on what file.                                           │
│   • Revolving doors — regulator ↔ regulated job moves, with       │
│     cooling-off facts.                                            │
│   • Industry associations' policy inputs: IBA, CII/ASSOCHAM/FICCI │
│     committees, think-tank funders in policy debates.             │
└────────────────────────────────────────────────────────────────────┘
```

## Why a stack, not three loose sites

The capture story only becomes visible when the layers join:

- **RegTrac ↔ SROTrac**: a regulator "outsources" consensus-building (fees, codes,
  grievance standards) to an SRO → SROTrac shows *who is inside that SRO*.
  Example on record: the RBI's SRO-FT framework (draft Jan 2024) produced
  FACE (Aug 2024) and UFF (Sep 2026) — the second recognition arrived while RBI
  leadership itself was newly reconstituted (RegTrac leadership table).
- **SROTrac ↔ LobbyWatch**: SRO members are the same institutions that flood
  consultation processes. A rule that survives consultation unchanged toward
  industry comments is a LobbyWatch finding; the membership that wanted it is a
  SROTrac fact.
- **LobbyWatch ↔ RegTrac**: appointment authorities (Appointments Committee of
  the Cabinet; Financial Sector Regulatory Appointments Search Committee) are
  RegTrac rows. The revolving door lands people from Room 3 into Room 1.

## Ground rules for all three layers

1. Public data first: statutes, gazettes, RTI, published rosters, regulator websites.
2. Every claim sourced; leadership claims sourced per-row with dates.
3. "As of" stamped everywhere; corrections visible, never silent.
4. Consumer payoff required: each page answers "why should the person paying care".
5. No insinuation without a paper trail — access and influence are documented
   through meetings, minutes, comment letters and appointment orders, not vibes.

## LobbyWatch build order (when picked up)

1. Scraper: consultation-paper indexes of RBI, SEBI, IRDAI, PFRDA, IBBI, IFSCA
   (each has a "consultations" section; formats vary wildly).
2. Comments corpus: download published comments; RTI the unpublished ones
   (template RTI: "copies of comments received on [paper no.] and minutes of the
   committee that considered them").
3. Diff engine: draft clause → final clause → which commenter's language appears.
4. Revolving-door ledger: regulator officials' post-retirement appointments
   (PSU boards, regulated entities, SRO governing councils) from press + MCA filings.
5. Publish: one page per consultation, timeline of access, scorecard per regulator
   on comment transparency.

*RegTrac and SROTrac are live; this document is the contract for the third layer.*
