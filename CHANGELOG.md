# Changelog

Alle væsentlige ændringer til dette skill dokumenteres her. Følger [Keep a Changelog](https://keepachangelog.com/da/) og [SemVer](https://semver.org/lang/da/).

## [Uudgivet]

### Tilføjet
- GitHub Actions-lint: Python-syntakstjek, SKILL.md-frontmatter-validering og scan mod committede API-nøgler.
- `scripts/aktivitet.py`: samler git-commits og agent-transskripter til en markdown-rapport, så tidsregistreringer bygger på evidens. Slår worktrees og kloner sammen og markerer automatik-sessioner som `[LOOP]`.
- Afsnit om **klokkeslæt** (`startTime`/`endTime`), inkl. at API'et kun accepterer UTC med `Z` og afviser offset-formen.
- Afsnit om **at finde ud af hvad der faktisk blev lavet**, med reglerne for hvordan aktiv tid og commit-antal skal læses.
- Afsnit med **verificerede faldgruber**: `PATCH` mister klienten uden `clientId`, svar udfolder ikke `client`, `billableRate` skal være streng, `limit` kappes tavst ved 100, og danske tegn på Windows.

### Ændret
- Arbejdsgangen for logning nævner nu klokkeslæt, klientens sats og `limit`-loftet.
- Tre nye red flags: `PATCH` uden `clientId`, timer udledt af commit-antal eller loop-sessioner, og oversete sider i pagineringen.

## [1.0.0] — 2026-06-22

### Tilføjet
- Første offentlige udgivelse.
- Log tidsregistreringer (enkeltvis + batch) med minut-præcision.
- Læs rapporter: tidssum og omsætning pr. klient/projekt.
- Håndtér fakturaer (opret/send/markér betalt) og klippekort.
- Slå klienter, projekter og opgaver op; start/stop timer.
- Konfigurérbar adfærd: bekræft-før-oprettelse, minutter vs. decimaltimer, konservative estimater, auto-opdagelse, maks entries pr. kørsel.
- Guardrails: aldrig slette utilsigtet, kun udpeget klient, maks-grænse pr. kørsel, nøgle logges aldrig.
- Fejlhåndtering for 401/403/429/øvrige.
- Valgfri Python-stdlib-helper (`timetrack.py`) + ren `curl`-vej.
- Install-guide for Claude Code, Codex og generiske agenter.
