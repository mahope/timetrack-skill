# Kom-i-gang-prompt (til hjemmesiden)

Når en kunde har oprettet sin API-nøgle på timetrack.dk, kan de kopiere prompten herunder ind i Claude Code, Codex eller en anden agent for at komme i gang med det samme. Erstat `tk_live_DIN_NØGLE`.

---

```
Jeg vil bruge TimeTrack-skillet til at styre min tidsregistrering.

Installér skillet hvis det ikke allerede er der:
  git clone https://github.com/mahope/timetrack-skill ~/.claude/skills/timetrack
(Codex: brug ~/.agents/skills/timetrack i stedet.)

Gem min API-nøgle lokalt (commit den aldrig):
  echo "TIMETRACK_API_KEY=tk_live_DIN_NØGLE" > ~/.timetrack-secret

Bekræft at det virker ved at hente min bruger (GET /me), og giv mig så et
kort overblik over hvad skillet kan. Spørg mig før du opretter noget.
```

---

Derefter kan kunden bare skrive ting som:
- "Registrér 40 minutter i dag på [klient] for [opgave]."
- "Hvad har jeg af ufakturerede timer denne måned?"
- "Start en timer på [projekt]."
