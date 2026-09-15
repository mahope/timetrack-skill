#!/usr/bin/env python3
"""Saml dagens (eller periodens) faktiske aktivitet fra git og agent-transskripter.

Formålet er at svare på "hvad blev der egentlig lavet?", så tidsregistreringer
bygger på evidens frem for hukommelse. Skriver en markdown-rapport til stdout.

Kun Python-stdlib. Skriver aldrig til dine repos — al git-brug er læsning.

Eksempler:
    python aktivitet.py --from 2026-09-10 --to 2026-09-15 --repos ~/Projects
    python aktivitet.py --repos ~/Projects --repos ~/work --out rapport.md
    python aktivitet.py --from 2026-09-14 --no-transcripts

Bemærk om tid: tallene under "aktiv tid" er summen af mellemrum mellem
beskeder i en session, hvor pauser over --gap minutter ikke tælles med. Det er
et *signal om hvad der blev arbejdet på*, ikke en stempelur-måling. Sessioner
der kører parallelt tælles hver for sig, så en dag kan overstige 24 timer.
Sessioner markeret [LOOP] er startet af en stop-hook eller lignende automatik
og er ikke hands-on-arbejde — tæl dem lavt eller slet ikke.
"""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

SKIP_DIRS = {
    "node_modules", ".next", "target", "vendor", "dist", "build",
    ".venv", "venv", "__pycache__", ".turbo", ".cache",
}
# Mapper der næsten altid er kopier af et andet repo (samme commits)
COPY_HINTS = ("worktrees", "_arkiv", "wt-", "wave-", ".claude/worktrees")


def parse_day(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def find_repos(roots, max_depth):
    """Find git-repos under roots. Returnerer absolutte stier."""
    repos = []
    for root in roots:
        root = os.path.abspath(os.path.expanduser(root))
        if not os.path.isdir(root):
            print("advarsel: springer over (findes ikke): %s" % root, file=sys.stderr)
            continue
        base = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            depth = dirpath.count(os.sep) - base
            if ".git" in dirnames or ".git" in filenames:
                repos.append(dirpath)
            if ".git" in dirnames:
                dirnames.remove(".git")
            if depth >= max_depth - 1:
                dirnames[:] = []
            else:
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    return repos


def git_log(repo, d0, d1):
    """Commits med author-dato i [d0, d1] som (hash, dato, tid, forfatter, emne).

    git --since/--until filtrerer på committer-dato, mens vi rapporterer på
    author-dato (hvornår arbejdet blev skrevet). De to kan afvige efter rebase
    eller merge, så vi henter et døgn ekstra i hver ende og filtrerer præcist
    her — ellers dukker der commits op uden for den periode brugeren bad om.
    """
    lo = (d0 - timedelta(days=1)).isoformat()
    hi = (d1 + timedelta(days=1)).isoformat()
    cmd = [
        "git", "-C", repo, "log", "--all",
        "--since=%sT00:00:00" % lo, "--until=%sT23:59:59" % hi,
        "--date=format:%Y-%m-%d %H:%M", "--format=%H|%ad|%an|%s",
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=60)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if p.returncode != 0:
        return None
    out = []
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        h, ad, an, subject = parts
        day, _, hhmm = ad.partition(" ")
        if not (d0.isoformat() <= day <= d1.isoformat()):
            continue
        out.append((h, day, hhmm, an, subject))
    return out


def dedupe_repos(repo_logs):
    """Slå repos sammen der har præcis samme commit-sæt (worktrees og kloner).

    Beholder den sti der ser mindst ud som en kopi, derefter den korteste.
    """
    def copy_score(path):
        low = path.replace("\\", "/").lower()
        return (any(h in low for h in COPY_HINTS), len(path))

    by_hashes = defaultdict(list)
    for repo, commits in repo_logs.items():
        if not commits:
            continue
        by_hashes[frozenset(c[0] for c in commits)].append(repo)
    primary = {}
    dupes = []
    for _, repos in by_hashes.items():
        repos.sort(key=copy_score)
        primary[repos[0]] = repo_logs[repos[0]]
        dupes.extend(repos[1:])
    return primary, dupes


def short(path, roots):
    p = os.path.abspath(path)
    for root in roots:
        root = os.path.abspath(os.path.expanduser(root))
        if p.startswith(root):
            rel = p[len(root):].lstrip(os.sep)
            return (rel or os.path.basename(root)).replace(os.sep, "/")
    return p.replace(os.sep, "/")


def read_sessions(transcript_root, d0, d1, gap_minutes, tz_offset):
    """Aktiv tid pr. dag pr. arbejdsmappe ud fra agent-transskripter (JSONL)."""
    tz = timezone(timedelta(hours=tz_offset))
    gap = gap_minutes * 60
    root = os.path.abspath(os.path.expanduser(transcript_root))
    if not os.path.isdir(root):
        return {}
    floor = datetime.combine(d0, datetime.min.time()).timestamp() - 86400
    per_day = defaultdict(dict)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".jsonl"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                if os.path.getmtime(path) < floor:
                    continue
            except OSError:
                continue
            stamps, cwd, prompts, is_loop = [], None, [], False
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        cwd = obj.get("cwd") or cwd
                        ts = obj.get("timestamp")
                        when = None
                        if ts:
                            try:
                                when = datetime.fromisoformat(
                                    ts.replace("Z", "+00:00")).astimezone(tz)
                            except Exception:
                                when = None
                        if when:
                            stamps.append(when)
                        if obj.get("type") == "user":
                            content = (obj.get("message") or {}).get("content")
                            if isinstance(content, list):
                                content = " ".join(
                                    b.get("text", "") for b in content
                                    if isinstance(b, dict) and b.get("type") == "text")
                            if isinstance(content, str) and content.strip():
                                text = " ".join(content.split())
                                if text.startswith("<"):
                                    continue
                                if "Stop hook is now active" in text:
                                    is_loop = True
                                    continue
                                if text.startswith("Base directory for this skill"):
                                    continue
                                if len(prompts) < 3:
                                    prompts.append(text[:120])
            except OSError:
                continue
            if not stamps or not prompts:
                continue
            by_day = defaultdict(list)
            for when in stamps:
                if d0 <= when.date() <= d1:
                    by_day[when.date()].append(when)
            key = (cwd or "ukendt").replace(os.sep, "/")
            for day, times in by_day.items():
                times.sort()
                active = sum(
                    (b - a).total_seconds()
                    for a, b in zip(times, times[1:])
                    if (b - a).total_seconds() <= gap)
                hours = round(active / 3600 * 4) / 4
                if hours <= 0:
                    continue
                slot = per_day[day].setdefault(
                    key, {"hours": 0.0, "sessions": 0, "loop": 0.0,
                          "first": None, "last": None, "prompts": []})
                slot["hours"] += hours
                slot["sessions"] += 1
                if is_loop:
                    slot["loop"] += hours
                first, last = times[0].strftime("%H:%M"), times[-1].strftime("%H:%M")
                slot["first"] = min(slot["first"], first) if slot["first"] else first
                slot["last"] = max(slot["last"], last) if slot["last"] else last
                for text in prompts:
                    if len(slot["prompts"]) < 3 and text not in slot["prompts"]:
                        slot["prompts"].append(text)
    return per_day


def main():
    today = date.today().isoformat()
    ap = argparse.ArgumentParser(
        description="Saml git- og agent-aktivitet som grundlag for tidsregistrering.")
    ap.add_argument("--from", dest="d0", default=today, help="startdato (YYYY-MM-DD)")
    ap.add_argument("--to", dest="d1", default=None, help="slutdato (default: samme som --from)")
    ap.add_argument("--repos", action="append", default=None,
                    help="rod at lede efter git-repos i (kan gentages, default: .)")
    ap.add_argument("--depth", type=int, default=4, help="hvor dybt der ledes efter repos")
    ap.add_argument("--transcripts", default="~/.claude/projects",
                    help="rod med agent-transskripter (JSONL)")
    ap.add_argument("--no-transcripts", action="store_true", help="spring transskripter over")
    ap.add_argument("--gap", type=int, default=30,
                    help="pause i minutter der afbryder aktiv tid (default 30)")
    ap.add_argument("--tz", type=float, default=2.0, help="timers forskydning fra UTC (default +2)")
    ap.add_argument("--out", default=None, help="skriv rapporten til fil i stedet for stdout")
    args = ap.parse_args()

    d0 = parse_day(args.d0)
    d1 = parse_day(args.d1) if args.d1 else d0
    if d1 < d0:
        ap.error("--to ligger før --from")
    roots = args.repos or ["."]

    lines = []
    w = lines.append
    w("# Aktivitet %s%s" % (d0, "" if d0 == d1 else " til %s" % d1))
    w("")

    repos = find_repos(roots, args.depth)
    repo_logs, failed = {}, []
    for repo in repos:
        commits = git_log(repo, d0, d1)
        if commits is None:
            failed.append(repo)
        elif commits:
            repo_logs[repo] = commits
    primary, dupes = dedupe_repos(repo_logs)

    w("## Commits")
    w("")
    if not primary:
        w("Ingen commits i perioden (%d repos gennemsøgt)." % len(repos))
    else:
        total = sum(len(c) for c in primary.values())
        w("%d commits i %d repos (%d kopier/worktrees slået sammen, %d repos gennemsøgt)."
          % (total, len(primary), len(dupes), len(repos)))
        w("")
        per_day_repo = defaultdict(lambda: defaultdict(list))
        for repo, commits in primary.items():
            for _, day, hhmm, author, subject in commits:
                per_day_repo[day][short(repo, roots)].append((hhmm, author, subject))
        w("| Dato | Repo | Antal | Tidsrum | Eksempler |")
        w("|---|---|---|---|---|")
        for day in sorted(per_day_repo):
            for repo in sorted(per_day_repo[day]):
                items = sorted(per_day_repo[day][repo])
                times = [i[0] for i in items]
                authors = {i[1] for i in items}
                examples = " · ".join(i[2][:60] for i in items[:3])
                who = "" if len(authors) == 1 else " (%s)" % ", ".join(sorted(authors))
                w("| %s | %s | %d%s | %s-%s | %s |" % (
                    day, repo, len(items), who, times[0], times[-1],
                    examples.replace("|", "\\|")))
    w("")

    if not args.no_transcripts:
        sessions = read_sessions(args.transcripts, d0, d1, args.gap, args.tz)
        w("## Agent-sessioner")
        w("")
        if not sessions:
            w("Ingen sessioner fundet under `%s`." % args.transcripts)
        else:
            w("Aktiv tid er et signal, ikke en måling. [LOOP] = automatik, ikke hands-on.")
            for day in sorted(sessions):
                day_total = sum(s["hours"] for s in sessions[day].values())
                day_loop = sum(s["loop"] for s in sessions[day].values())
                w("")
                w("### %s (%s) — %.2f t, heraf loop %.2f t"
                  % (day, day.strftime("%a"), day_total, day_loop))
                w("")
                ranked = sorted(sessions[day].items(), key=lambda kv: -kv[1]["hours"])
                for cwd, s in ranked:
                    if s["hours"] < 0.25:
                        continue
                    w("- **%.2f t** · %d sess. · %s-%s · `%s`%s" % (
                        s["hours"], s["sessions"], s["first"], s["last"], cwd,
                        "  [LOOP %.2f]" % s["loop"] if s["loop"] else ""))
                    for text in s["prompts"]:
                        w("  - %s" % text.replace("|", "\\|"))
        w("")

    if failed:
        w("## Repos der ikke kunne læses")
        w("")
        for repo in failed[:20]:
            w("- %s" % short(repo, roots))
        w("")

    report = "\n".join(lines)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
        print("skrev %s (%d linjer)" % (args.out, len(lines)))
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(report)


if __name__ == "__main__":
    main()
