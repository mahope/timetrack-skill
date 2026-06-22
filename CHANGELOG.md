# Changelog

Alle væsentlige ændringer til dette skill dokumenteres her. Følger [Keep a Changelog](https://keepachangelog.com/da/) og [SemVer](https://semver.org/lang/da/).

## [Uudgivet]

### Tilføjet
- GitHub Actions-lint: Python-syntakstjek, SKILL.md-frontmatter-validering og scan mod committede API-nøgler.

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
