#!/usr/bin/env python3
"""TimeTrack API-helper (kun Python-stdlib, ingen afhængigheder).

Nøgle hentes fra (i rækkefølge):
  1. miljøvariablen TIMETRACK_API_KEY
  2. ~/.timetrack-secret eller ./.timetrack-secret  (linje: TIMETRACK_API_KEY=tk_live_...)

Brug:
    python timetrack.py list   --client anna --from 2026-06-01 --to 2026-06-30
    python timetrack.py create --client anna --date 2026-06-22 --min 38 --desc "..."

'create' er bevidst én-ad-gangen og kræver eksplicitte args — ingen auto-gæt.
Foreslå altid for brugeren og få OK før du kører 'create' (se SKILL.md).
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://timetrack.dk/api/v1"

try:  # Windows-konsol er cp1252 — tving UTF-8 så æøå/→ ikke crasher
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def token() -> str:
    env = os.environ.get("TIMETRACK_API_KEY")
    if env and env.startswith("tk_live_"):
        return env.strip()
    for path in ("~/.timetrack-secret", "./.timetrack-secret"):
        p = os.path.expanduser(path)
        if os.path.exists(p):
            m = re.search(r"tk_live_[A-Za-z0-9]+", open(p, encoding="utf-8").read())
            if m:
                return m.group(0)
    sys.exit(
        "Ingen TimeTrack API-nøgle fundet.\n"
        "Sæt TIMETRACK_API_KEY=tk_live_... eller læg den i ~/.timetrack-secret.\n"
        "Opret en nøgle på timetrack.dk → Indstillinger → API-nøgler."
    )


def call(method: str, path: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
    )
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("401: Nøglen er ugyldig eller mangler. Opret en ny på timetrack.dk → Indstillinger → API-nøgler.")
        if e.code == 429:
            sys.exit(f"429: Rate limit. Prøv igen om {e.headers.get('Retry-After','et øjeblik')} sek.")
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:300]}")


def find_client(q: str) -> str:
    items = call("GET", f"/clients?q={urllib.parse.quote(q)}&limit=100").get("data", [])
    if not items:
        sys.exit(f"Ingen klient matcher '{q}'")
    if len(items) > 1:
        names = ", ".join(c["name"] for c in items)
        print(f"Flere klienter matcher '{q}': {names} — vælg mere præcist.", file=sys.stderr)
    return items[0]["id"]


def mins_to_hours(m: int) -> float:
    return round(m / 60, 2)


def main():
    p = argparse.ArgumentParser(description="TimeTrack API-helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="list tidsregistreringer for en periode")
    pl.add_argument("--client", required=True)
    pl.add_argument("--from", dest="frm", required=True)
    pl.add_argument("--to", required=True)

    pc = sub.add_parser("create", help="opret én tidsregistrering")
    pc.add_argument("--client", required=True)
    pc.add_argument("--date", required=True, help="YYYY-MM-DD")
    pc.add_argument("--min", type=int, required=True, help="minutter")
    pc.add_argument("--desc", required=True)
    pc.add_argument("--no-billable", dest="billable", action="store_false", default=True)

    a = p.parse_args()
    cid = find_client(a.client)

    if a.cmd == "list":
        items = call("GET", f"/time-entries?clientId={cid}&from={a.frm}&to={a.to}&limit=100").get("data", [])
        tot = 0
        for e in sorted(items, key=lambda x: x.get("date", "")):
            m = round(float(e.get("hours", 0)) * 60)
            tot += m
            print(f"{e.get('date','')[:10]} | {m:>3} min | {(e.get('description') or '')[:70]}")
        print(f"I alt: {tot} min = {tot/60:.2f} timer")

    elif a.cmd == "create":
        if a.min <= 0:
            sys.exit("--min skal være > 0")
        entry = call("POST", "/time-entries", {
            "clientId": cid, "date": a.date, "hours": mins_to_hours(a.min),
            "description": a.desc, "isBillable": a.billable,
        })
        print(f"OK {a.date} {a.min} min ({mins_to_hours(a.min)} t) — id={entry.get('data',{}).get('id','?')}")


if __name__ == "__main__":
    main()
