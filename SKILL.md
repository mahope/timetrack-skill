---
name: timetrack
description: Use when logging time, reviewing tracked hours, managing invoices/prepaid packages, or looking up clients/projects in TimeTrack (timetrack.dk) via its public API. Triggers — "registrer tid", "log timer", "før tid på [klient]", "start timer", "ufakturerede timer", "tid pr. klient", "ugeoverblik", "opret faktura", "TimeTrack".
---

# TimeTrack

Styr [TimeTrack](https://timetrack.dk) — dansk tidsregistrerings-SaaS — fra din agent via dens offentlige API. Log tid, læs rapporter, håndtér fakturaer/klippekort og slå klienter/projekter op.

> Sprog: dansk. Officiel API-reference (kanonisk, opdateres aldrig her): **https://timetrack.dk/api/v1/docs** · OpenAPI: `https://timetrack.dk/api/v1/openapi.json`. Henvis dertil for felter ud over kernen nedenfor.

## Konfiguration — rediger disse efter behov

```
bekræft_før_oprettelse: ja      # ja = foreslå og vent på OK før skrivning. nej = opret direkte.
tids_præcision: minutter        # minutter (fx 43 min) eller decimaltimer (fx 0,75 t)
konservative_estimater: nej     # ja = estimér lavt når du selv gætter tid
auto_opdag_opgaver: nej         # ja = scan git/samtale/noter for udført arbejde og foreslå entries
maks_entries_pr_kørsel: 20      # hård grænse pr. kørsel (guardrail)
```

## Kom godt i gang (engangsopsætning)

1. Log ind på timetrack.dk → **Indstillinger → API-nøgler** (`/dashboard/settings/api`) og opret en nøgle. Den starter med `tk_live_`.
2. Gør nøglen tilgængelig for agenten på **én** af disse måder:
   - **Env-variabel** (anbefalet): sæt `TIMETRACK_API_KEY=tk_live_...`
   - **Lokal fil**: gem linjen `TIMETRACK_API_KEY=tk_live_...` i `~/.timetrack-secret` (eller `./.timetrack-secret`). Læg den i `.gitignore` — commit den aldrig.
3. Test: `GET /me` skal svare med din bruger.

**Mangler/ugyldig nøgle?** Stop pænt og vis denne vejledning — gæt aldrig en nøgle og fortsæt ikke uden.

## Auth

Send nøglen som Bearer-token. Alle kald går mod base `https://timetrack.dk/api/v1`.

```bash
TT="${TIMETRACK_API_KEY:-$(grep -hoE 'tk_live_[A-Za-z0-9]+' ~/.timetrack-secret ./.timetrack-secret 2>/dev/null | head -1)}"
curl -s https://timetrack.dk/api/v1/me -H "Authorization: Bearer $TT"
```

## Kerne-endpoints

| Operation | Kald |
|-----------|------|
| Hvem er jeg | `GET /me` |
| Find klient | `GET /clients?q=navn` |
| Projekter | `GET /projects?clientId=…` · opret: `POST /projects` |
| Opgaver | `GET /tasks?clientId=…&status=…` |
| Liste tid | `GET /time-entries?clientId=…&from=YYYY-MM-DD&to=YYYY-MM-DD&limit=100` |
| **Opret tid** | `POST /time-entries` |
| Opret flere | `POST /time-entries/batch` |
| Timer | `GET /timer` (kører nu) · `POST /timer` (start) · `DELETE /timer` (stop) |
| Rapporter | `GET /reports/time-summary?clientId=…&from=…&to=…` · `GET /reports/revenue?…&groupBy=…` |
| Fakturaer | `GET /invoices` · `POST /invoices` · `POST /invoices/{id}/send` · `POST /invoices/{id}/mark-paid` |
| Klippekort | `GET /prepaid-packages` · `POST /prepaid-packages` |

**POST /time-entries body:** `clientId` (eller `projectId`), `date` (YYYY-MM-DD, påkrævet), `hours` (positivt tal, påkrævet), `description`, valgfrit `notes`, `startTime`, `endTime`, `isBillable`, `isBilled`, `taskId`, `billableRate`, `prepaidPackageId`.
Rediger: `PATCH /time-entries/{id}` · slet: `DELETE /time-entries/{id}`.
Øvrige felter/endpoints: se `/api/v1/docs`.

## Minutter ↔ hours

`hours` er `decimal(5,2)`. Konvertér med **`hours = round(minutter / 60, 2)`** (43 min → 0,72). Læs tilbage med `round(hours * 60)`.

## Klokkeslæt — så posten lander i kalenderen

Uden `startTime`/`endTime` findes posten kun i listen, ikke i TimeTracks kalendervisning. Sæt dem altid, medmindre brugeren kun kender et samlet antal timer.

- **Format: UTC med `Z`** — fx `2026-09-10T05:00:00.000Z`. Offset-formen (`…+02:00`) afvises med `422 Invalid ISO datetime`, selvom den er gyldig ISO 8601. Konvertér fra lokal tid først:

  ```python
  from datetime import datetime, timedelta, timezone
  local = timezone(timedelta(hours=2))            # dansk sommertid
  start = datetime(2026, 9, 10, 7, 0, tzinfo=local)
  start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")   # 05:00Z
  ```

- **`endTime` skal være efter `startTime`**, og blokken bør svare til `hours`.
- **Læg dagens blokke sekventielt uden overlap.** Overlappende blokke ser rodede ud i kalenderen, også når arbejdet reelt kørte parallelt.

## Faldgruber (verificeret mod produktion)

- **`PATCH` opfører sig som en delvis erstatning med bivirkninger.** Udelader du `clientId`, mister posten sin klient, og `billableRate` genberegnes fra din default-sats. Send derfor **altid** `clientId`, `date`, `hours`, `description` og `billableRate` med, også når du kun vil rette ét felt — og **læs posten tilbage bagefter**.
- **`PATCH`- og `POST`-svar udfolder ikke `client`-objektet.** Feltet ser tomt ud, selvom `clientId` er sat korrekt. Verificér med et `GET` frem for at stole på svaret.
- **`billableRate` skal sendes som streng** (`"900"`, ikke `900`). Tal kasseres tavst, og posten får klientens sats i stedet. Tjek klientens sats først, og send kun feltet når du bevidst vil afvige.
- **`limit` kappes tavst ved 100.** Beder du om 500, får du 100 uden fejl. Læs `pagination.totalPages` og hent side 2+ med `page=`, ellers mister du poster uden at opdage det.
- **Danske tegn på Windows:** send bodyen som `json.dumps(body, ensure_ascii=True)` fra Python. Både inline `curl -d` og `--data-binary @fil` ødelægger æ/ø/å. Verificér efter skrivning: `sorted(set(hex(ord(c)) for c in desc if ord(c) > 127))` skal give `0xe5/0xe6/0xf8` — aldrig `0xc3`-par eller `0xef/0xbf/0xbd`.

## Find ud af hvad der faktisk blev lavet

Det svære ved tidsregistrering er sjældent API-kaldet, men at huske hvad dagen gik med. `scripts/aktivitet.py` (kun stdlib) samler evidensen:

```bash
python scripts/aktivitet.py --from 2026-09-10 --to 2026-09-15 --repos ~/Projects
```

Den finder git-repos under de angivne rødder, slår worktrees og kloner sammen (samme commit-sæt tælles én gang), og læser agent-transskripter fra `~/.claude/projects` for aktiv tid pr. arbejdsmappe pr. dag.

**Sådan læses tallene:**

- Aktiv tid er *et signal om hvad der blev arbejdet på*, ikke en stempelur-måling. Parallelle sessioner tælles hver for sig, så en dag kan overstige 24 timer.
- Sessioner markeret `[LOOP]` er startet af automatik (stop-hook, natteloop). **De er ikke hands-on-arbejde** — tæl dem lavt eller slet ikke.
- Mange commits betyder ikke mange timer. En agent-drevet oprydning på tværs af ti repos kan være 200 commits og halvanden times tilsyn.
- Brugeren beder ofte selv om et konkret antal minutter undervejs ("track 15 minutter på det"). Søg efter den slags i transskriptet før du gætter — og tjek om posten allerede findes.

## Arbejdsgang — log tid

1. `GET /clients?q=…` → find `clientId` (gæt aldrig id'er). Notér klientens sats.
2. `GET /time-entries?clientId=…&from=…&to=…` → se eksisterende, undgå dubletter. Husk `limit`-loftet på 100.
3. Saml det udførte arbejde (kun `auto_opdag_opgaver: ja` → `scripts/aktivitet.py`, se ovenfor).
4. Hvis `bekræft_før_oprettelse: ja` → **foreslå** en tabel (dato · klokkeslæt · opgave · tid) og **vent på OK**. Ellers opret direkte.
5. `POST /time-entries` (eller `/batch`) med `startTime`/`endTime` i UTC. Overhold `maks_entries_pr_kørsel` — flere poster end grænsen køres i flere omgange efter aftale.
6. **Verificér**: list perioden igen og vis tiden tilbage, inkl. klient, sats og klokkeslæt.

`timetrack.py` (valgfri, kun Python-stdlib) har `list` og `create` klar. Ren `curl` virker også uden afhængigheder.

## Guardrails (gælder altid)

- **Slet/overskriv aldrig** entries uden brugeren eksplicit beder om netop det.
- **Kun den klient brugeren udpeger** — rør aldrig andre klienters data.
- **Maks `maks_entries_pr_kørsel`** skrivninger pr. kørsel; over det → stop og bekræft.
- **Foreslå før du skriver**, medmindre `bekræft_før_oprettelse: nej`.
- **Log aldrig API-nøglen** i output, kommandoer der ekkoes, eller fejlbeskeder.

## Fejlhåndtering

| Status | Betyder | Gør |
|--------|---------|-----|
| 401 | Nøgle mangler/ugyldig | Stop, vis "Kom godt i gang"-vejledningen |
| 403 | Nøglen mangler scope | Forklar hvilken adgang der kræves |
| 429 | Rate limit | Vent jf. `Retry-After`-header, forklar på dansk |
| 4xx/5xx | Andet | Vis API'ets fejlbesked oversat til dansk, gæt ikke videre |

## Red flags — STOP

- Du er ved at `POST`/`DELETE` uden bekræftelse (når `bekræft_før_oprettelse: ja`) → foreslå først.
- Du sætter runde hele timer hvor `tids_præcision: minutter` → brug minutter.
- Du opretter uden at have tjekket eksisterende entries → risiko for dublet.
- Du er på vej til at slette noget → stop, det er aldrig default.
- Du `PATCH`'er uden at sende `clientId` med → posten mister sin klient og sats.
- Du udleder timer direkte fra commit-antal eller fra en `[LOOP]`-session → det er ikke hands-on-tid.
- Du fik færre poster tilbage end ventet → tjek `pagination.totalPages` før du konkluderer at der ikke er mere.

## Support

Fejl eller forslag: opret et issue på skillets GitHub-repo. API-spørgsmål: `https://timetrack.dk/api/v1/docs`.
