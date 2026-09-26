#!/usr/bin/env bash
# RegTrac daily refresh: re-fetch regulator homepages (social-drift snapshots),
# rebuild the site, run the social drift check, commit & push on change.
# Designed to be run by the daily automation agent (and safe to run by hand).
set -uo pipefail
cd "$(dirname "$0")/.."

UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
RAW=data/raw
fetch() { # fetch <url> <outfile>
  curl -sL --max-time 40 -A "$UA" "$1" -o "$2" && [ -s "$2" ]
}

FAILED=0
# Homepage snapshots backing the social-presence drift check. Failures are
# non-fatal: a stale snapshot keeps the previous verdict, the check just skips
# a beat. npcI + nabard block plain curl (Akamai / cookie wall) — the refresh
# agent may top these up via agent-browser when the snapshot is missing.
fetch "https://www.rbi.org.in"    "$RAW/rbi.html"    || { echo "FETCH FAIL rbi";    FAILED=1; }
fetch "https://www.sebi.gov.in"   "$RAW/sebi.html"   || { echo "FETCH FAIL sebi";   FAILED=1; }
fetch "https://irdai.gov.in"      "$RAW/irdai.html"  || { echo "FETCH FAIL irdai";  FAILED=1; }
fetch "https://pfrda.org.in"      "$RAW/pfrda.html"  || { echo "FETCH FAIL pfrda";  FAILED=1; }
fetch "https://ibbi.gov.in"       "$RAW/ibbi.html"   || { echo "FETCH FAIL ibbi";   FAILED=1; }
fetch "https://ifsca.gov.in"      "$RAW/ifsca.html"  || { echo "FETCH FAIL ifsca";  FAILED=1; }
fetch "https://www.nabard.org"    "$RAW/nabard.html" || { echo "FETCH FAIL nabard (blocks curl; optional)"; }
fetch "https://dicgc.org.in"      "$RAW/dicgc.html"  || { echo "FETCH FAIL dicgc";  FAILED=1; }
fetch "https://nhb.org.in"        "$RAW/nhb.html"    || { echo "FETCH FAIL nhb";    FAILED=1; }
fetch "https://sidbi.in"          "$RAW/sidbi.html"  || { echo "FETCH FAIL sidbi";  FAILED=1; }
fetch "https://nfra.gov.in"       "$RAW/nfra.html"   || { echo "FETCH FAIL nfra";   FAILED=1; }
fetch "https://www.npci.org.in"   "$RAW/npci.html"   || { echo "FETCH FAIL npci (Akamai; optional)"; }

python3 scripts/build.py       || exit 1
python3 scripts/bloggen.py     || exit 1
python3 scripts/social_check.py || echo "SOCIAL CHECK FAIL (non-fatal)"

if [ -n "$(git status --porcelain -- data ':(exclude)data/raw' '*.html' blog css)" ]; then
  git add -A
  git -c user.name="RegTrac bot" -c user.email="cashlessconsumerin@gmail.com" \
    commit -q -m "Daily refresh $(date -u +%F-%H%M) UTC — homepage re-fetch + rebuild + social drift check"
  git pull --rebase -q origin main && git push -q origin main && echo "PUSHED: changes found and deployed"
else
  echo "NO-CHANGE: register, leadership and social links unchanged"
fi
[ "$FAILED" = "0" ] && echo "REFRESH OK" || echo "REFRESH DONE (with fetch failures)"
