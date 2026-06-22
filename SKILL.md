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

**POST /time-entries body:** `clientId` (eller `projectId`), `date` (YYYY-MM-DD, påkrævet), `hours` (positivt tal, påkrævet), `description`, valgfrit `notes`, `isBillable`, `isBilled`, `taskId`, `prepaidPackageId`.
Øvrige felter/endpoints: se `/api/v1/docs`.

## Minutter ↔ hours

`hours` er `decimal(5,2)`. Konvertér med **`hours = round(minutter / 60, 2)`** (43 min → 0,72). Læs tilbage med `round(hours * 60)`.

## Arbejdsgang — log tid

1. `GET /clients?q=…` → find `clientId` (gæt aldrig id'er).
2. `GET /time-entries?clientId=…&from=…&to=…` → se eksisterende, undgå dubletter.
3. Saml det udførte arbejde (kun `auto_opdag_opgaver: ja` → scan git/noter).
4. Hvis `bekræft_før_oprettelse: ja` → **foreslå** en tabel (dato · opgave · tid) og **vent på OK**. Ellers opret direkte.
5. `POST /time-entries` (eller `/batch`). Overhold `maks_entries_pr_kørsel`.
6. **Verificér**: list perioden igen og vis tiden tilbage.

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

## Support

Fejl eller forslag: opret et issue på skillets GitHub-repo. API-spørgsmål: `https://timetrack.dk/api/v1/docs`.
