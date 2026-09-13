"""Editorial-desk notes for entities that have no deep-dive content/reg-<id>.md file.

The seven statutory-core regulators compose their briefs from `content/reg-<id>.md`
(headings: Powers that matter / For the person paying / Watchpoints). The six
adjacent + context entities keep their notes here so there is exactly one source
of truth per entity.

Every bullet below is grounded in `data/regulators.csv` (statute, mandate,
grievance, website) — the composer attaches the entity's own site as the source.
Nothing here is a claim the register does not already carry.
"""

NOTES = {
    "dicgc": {
        "dek": "The backstop nobody thinks about until a bank fails: a Rs 5 lakh promise standing behind every deposit.",
        "why": [
            "DICGC is wholly owned by the RBI and insures deposits — cover stands at Rs 5 lakh per depositor, per bank, per right of the depositor, raised from Rs 1 lakh with effect from 4 February 2020.",
            "It is an insurer of last resort, not a conduct regulator: it does not supervise banks and cannot order a bank to behave differently.",
            "Premium is paid by insured banks, not by depositors, so the consumer's entire relationship with DICGC is passive — cover exists whether or not anyone knows about it.",
        ],
        "watch": [
            "Cover has not moved from Rs 5 lakh since February 2020 while nominal deposits have grown — the real value of the guarantee has been eroding quietly.",
            "There is no direct consumer channel to DICGC: claims are routed through the failed bank's liquidator and related disputes go to the RBI Ombudsman, which puts the payout timeline outside the depositor's control.",
            "RegTrac's register logs no sourced change at DICGC since it was built — for a backstop this quiet, that is itself the finding.",
        ],
    },
    "nhb": {
        "dek": "Built to grow housing finance, then stripped of the rulebook it was built around.",
        "why": [
            "Housing finance company regulation moved to the RBI on 9 August 2019, so NHB now refinances and develops the housing-finance market rather than supervising it.",
            "Its statutory footing (NHB Act, 1987) is unchanged, which means the institution kept the mandate language but lost the conduct powers that made the mandate enforceable.",
            "A home-loan borrower's complaint therefore lands with the RBI Ombudsman, not with the housing bank.",
        ],
        "watch": [
            "The split model — refinance at NHB, supervision at RBI — leaves no single body accountable for housing-finance market conduct.",
            "No consumer grievance route terminates at NHB itself; HFC complaints now sit under the RBI Ombudsman.",
            "RegTrac's register logs no sourced change at NHB since it was built, though the 2019 transfer remains the defining fact on its page.",
        ],
    },
    "sidbi": {
        "dek": "MSME development finance, deliberately not a conduct regulator.",
        "why": [
            "SIDBI is a development finance institution: refinance, fund of funds and market development for MSMEs, not retail supervision.",
            "Its statutory basis is the SIDBI Act, 1989, with operations from 2 April 1990, and it sits under the Ministry of Finance rather than the regulatory architecture.",
            "Because it does not regulate lenders, it cannot adjudicate a dispute between an MSME and its bank.",
        ],
        "watch": [
            "Borrower disputes go back to the lender or the RBI's ombudsman routes — SIDBI's own desk only covers direct borrowers.",
            "Development-finance institutions publish far less than regulators do, so the accountability gap here is transparency, not enforcement.",
            "RegTrac's register logs no sourced change at SIDBI since it was built.",
        ],
    },
    "nfra": {
        "dek": "Audit oversight with real enforcement teeth and no door for the public.",
        "why": [
            "NFRA was constituted in 2018 under section 132 of the Companies Act, 2013, to oversee auditors and audit firms of listed and large unlisted companies.",
            "It enforces accounting and auditing standards — its orders land on professionals rather than on consumers directly.",
            "It is statutory-adjacent in RegTrac's register: a financial-reporting watchdog under the Ministry of Corporate Affairs, not the finance ministry's regulatory core.",
        ],
        "watch": [
            "NFRA publishes no retail grievance channel; the only path to raise a concern runs through the audit regulator's own process after the fact.",
            "Enforcement-led oversight means the public learns of audit failure mainly through orders, not through routine disclosure.",
            "RegTrac's register logs no sourced change at NFRA since it was built.",
        ],
    },
    "fsdc": {
        "dek": "The apex body where regulators meet the Finance Minister — with no statute, and largely unpublished minutes.",
        "why": [
            "FSDC has no statute: it was created by executive resolution in 2010 and is chaired ex officio by the Union Finance Minister.",
            "It coordinates financial stability, inter-regulator disputes, financial literacy and inclusion councils, and a cyber security forum — the venue where cross-regulator positions get settled.",
            "Because it is non-statutory, RegTrac carries it as flagged context rather than as part of the regulator register.",
        ],
        "watch": [
            "Minutes are largely unpublished, so the coordination that shapes policy is invisible even though the participants are named public bodies.",
            "There is no public grievance channel and no statutory route to seek FSDC records.",
            "RegTrac's register logs no sourced change at FSDC since it was built.",
        ],
    },
    "npci": {
        "dek": "Everyone assumes it is a regulator. It is not: NPCI is a Section 8 company that runs UPI.",
        "why": [
            "NPCI is a not-for-profit company incorporated in 2008 and founded by the RBI and the Indian Banks' Association — it is not a statutory authority.",
            "It operates the retail payment rails (UPI, IMPS, NACH, RuPay, AePS, NETC) as an RBI-authorised payment system operator under the Payment and Settlement Systems Act, 2007.",
            "The practical consequence: a consumer cannot appeal to NPCI as a regulator, only escalate through a PSP or bank and then to the RBI Ombudsman.",
        ],
        "watch": [
            "Rail-level decisions — transaction limits, uptime, dispute turnaround — are made by a private company whose governance the public cannot inspect the way it inspects a statutory regulator.",
            "The escalation ladder for a failed UPI transaction ends at the RBI Ombudsman, which means the operator of the rail is not the body that answers for it.",
            "RegTrac's register logs no sourced change at NPCI since it was built, despite UPI volumes being the most consequential numbers in Indian retail finance.",
        ],
    },
}

# Layer links: how each regulator connects to the other sousveillance layers.
LAYER_LINKS = {
    "rbi": "The RBI *recognises* India's fintech SROs — FACE and UFF — so who sits inside them decides how industry consensus forms: [SROTrac](https://srotrac.cashlessconsumer.in) tracks those rosters.",
    "sebi": "SEBI-recognised SROs (AMFI, ANMI, BASL) sit in SROTrac's future scope: [SROTrac](https://srotrac.cashlessconsumer.in).",
    "irdai": "Insurance industry bodies that SEBI and IRDAI interface with are tracked alongside the recognised SROs in [SROTrac](https://srotrac.cashlessconsumer.in).",
    "ifsca": "IFSCA's SRO framework applications and the entities that comment on them are the rule-borrower layer: [SROTrac](https://srotrac.cashlessconsumer.in).",
    "npci": "NPCI sits between the regulator and the industry: the firms that shape its rules through their associations are tracked in [SROTrac](https://srotrac.cashlessconsumer.in).",
}
LAYER_LINK_DEFAULT = (
    "Who lobbies these decisions, and what consultation comments were filed, is the missing "
    "third layer — LobbyWatch (planned) — because regulators here do not systematically publish "
    "their comment trails; the accountability gaps are catalogued in the "
    "[RegTrac register](https://regtrac.cashlessconsumer.in/regulators.html)."
)
