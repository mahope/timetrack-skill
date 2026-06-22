# TimeTrack agent-skill

Et [agent-skill](https://agentskills.io) der lader AI-agenter styre [TimeTrack](https://timetrack.dk) — dansk tidsregistrerings-SaaS — via dens offentlige API. Log tid, læs rapporter, håndtér fakturaer og klippekort, og slå klienter/projekter op, direkte fra din agent.

Virker med **Claude Code**, **Codex** og andre agenter der understøtter skills.

## Hvad det kan

- 🕒 Logge tidsregistreringer (minut-præcist, enkeltvis eller batch)
- 📊 Læse rapporter (ugeoverblik, ufakturerede timer, tid/omsætning pr. klient)
- 🧾 Håndtere fakturaer og klippekort
- 🔎 Slå klienter, projekter og opgaver op
- ⏱️ Starte/stoppe timer

Alt med indbyggede guardrails: foreslå før skrivning, aldrig slette utilsigtet, kun den klient du udpeger, og din API-nøgle logges aldrig.

## Installation

Du skal bruge en TimeTrack-konto og en API-nøgle.

**1. Opret en API-nøgle**
Log ind på timetrack.dk → **Indstillinger → API-nøgler** → opret. Nøglen starter med `tk_live_`.

**2. Gør nøglen tilgængelig**
Sæt env-variablen `TIMETRACK_API_KEY=tk_live_...`, eller gem linjen i `~/.timetrack-secret`. Commit den aldrig.

**3. Installér skillet**

| Runtime | Sådan |
|---------|-------|
| **Claude Code** | Klon ind i `~/.claude/skills/timetrack/` (eller installér som plugin). Aktiveres automatisk på relevante opgaver. |
| **Codex** | Klon ind i `~/.codex/skills/timetrack/` eller den fælles `~/.agents/skills/timetrack/`. |
| **Andre agenter** | Peg din agent på `SKILL.md`. Kernen er rene HTTP-kald (`curl`), så enhver agent der kan køre shell/HTTP kan bruge det. |

```bash
git clone https://github.com/mahope/timetrack-skill ~/.claude/skills/timetrack
```

## Hurtig start

Når nøglen er sat, så sig til din agent:

> "Registrér 35 minutter i dag på [klient] for [opgave] i TimeTrack."

eller

> "Hvad har jeg registreret på [klient] denne uge?"

Agenten foreslår, du bekræfter, og den opretter — se `SKILL.md` for den fulde arbejdsgang og konfiguration.

## Konfiguration

Øverst i `SKILL.md` er der en config-blok du kan tilpasse: bekræft-før-oprettelse, minutter vs. decimaltimer, konservative estimater, auto-opdagelse af opgaver, og maks antal entries pr. kørsel.

## Brug uden helper

Helperen `timetrack.py` (kun Python-stdlib) er valgfri. Alt kan også gøres med ren `curl` — se `SKILL.md`.

## API-dokumentation

Kanonisk API-reference: **https://timetrack.dk/api/v1/docs** · OpenAPI: `https://timetrack.dk/api/v1/openapi.json`

## Support

Fejl eller forslag: [opret et issue](https://github.com/mahope/timetrack-skill/issues).

## Licens

[MIT](LICENSE) © Mahope / Mads Holst Jensen
