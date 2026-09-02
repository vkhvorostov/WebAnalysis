# AGENTS.md — WebAnalysis

Guide for LLM coding agents working in this repository.

## Project purpose

WebAnalysis collects and stores structured metadata about company websites:

- CMS, language, HTTP framework, external JS, social links
- Domain registration date (WHOIS)
- HTML snapshots and JSON sidecars on disk under `ParsedData/`

The primary interface is a **FastAPI** app (`app.py`). Batch/CLI workflows use `Main.py` and CSV input.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| API | FastAPI + Uvicorn |
| DB | PostgreSQL + SQLAlchemy 2.x |
| Migrations | Alembic |
| HTTP fetch | `requests` (`HtmlParser.py`) |
| Screenshots | Selenium + Chrome (`ScreenshotMaker.py`) |
| WHOIS | `python-whois` + system `whois` CLI fallback (`DomainWhois.py`) |
| Container | Docker Compose (Postgres, Adminer, API) |

Python **3.11**. Dependencies are pinned in `requirements.txt`.

---

## Repository layout

```
app.py              # FastAPI routes and Pydantic models
Main.py             # Core analyze pipeline: process(db, company, parse_date)
SqlORM.py           # SQLAlchemy models (Company, CompanyData) + PostgresDB wrapper
SimpleSaver.py      # ParsedData paths, read/write HTML/JSON on disk
DomainWhois.py      # URL → domain, WHOIS → domain_created date
HtmlParser.py       # Fetch page HTML via requests
DeepCodeAnalyser.py # CMS / language / framework detection
JSAnalyser.py       # External JS and social link extraction
ScreenshotMaker.py  # Headless Chrome screenshot + page source
SetUrl.py           # CLI: backfill URLs from CSV into existing companies
MainCompare.py      # CLI: compare two parse folders for a company
MainGis.py / Gis.py # Legacy GIS-related scripts (not used by API)
alembic/            # DB migrations (source of truth for schema)
docker-compose.yml  # db + adminer + api
companies.csv       # Semicolon-delimited seed data (gitignored pattern: /*.csv)
ParsedData/         # On-disk parse artifacts (gitignored)
```

---

## Architecture

### Two storage layers (important)

1. **PostgreSQL** — canonical company identity + historical analysis rows.
2. **`ParsedData/`** — raw HTML, JSON, screenshots per parse date.

These are **not automatically kept in sync** on DELETE:

- `DELETE /companies/{id}` and data DELETE endpoints remove **DB rows only**.
- Files under `ParsedData/` are **never deleted** by the API.

### Data model

**`companies`** — one row per business entity:

| Column | Notes |
|--------|--------|
| `id` | PK |
| `company_name` | `/` normalized to `-` on insert |
| `city`, `industry` | Part of natural key used in lookups |
| `url` | Required; used for live fetch and WHOIS |

**`companies_data`** — time-series snapshots:

| Column | Notes |
|--------|--------|
| `id` | PK |
| `company_id` | FK → `companies.id` |
| `date_parse` | Calendar date of the snapshot |
| `cms`, `language`, `framework` | Strings |
| `external_js`, `social_links` | Text (often JSON-like strings) |
| `domain_created` | WHOIS registration date |

**Latest snapshot** for list/detail endpoints: `ORDER BY date_parse DESC, id DESC LIMIT 1`.

### ParsedData path convention

```
ParsedData/{industry}/{city}/{company_name}/{dd.mm.yyyy}/
  {company_name}.html
  {company_name}.json
  {company_name}_screenshot.png
```

- Live analyze (`parse_date=None`): creates **today's** folder (`datetime.now()`).
- Disk re-analyze (`parse_date` set): reads existing folder for that date; **no internet fetch**.
- API JSON field is `"date": "YYYY-MM-DD"` → maps to folder `dd.mm.yyyy`.

---

## Core pipeline: `Main.process`

Signature:

```python
process(db: PostgresDB, company: Company, parse_date: Optional[date] = None) -> Tuple[bool, Optional[str]]
```

Returns `(True, None)` on success or `(False, error_message)`.

### Modes

| `parse_date` | Source | Disk | DB write |
|--------------|--------|------|----------|
| `None` | Internet (`HtmlParser`, `ScreenshotMaker`) | Writes today's folder | **Insert** new `companies_data` row |
| Set | `ParsedData/.../{date}/` HTML + JSON | Read only | **Upsert** by `(company_id, date_parse)` |

Both modes call `get_domain_created_date(company.url)` and store `domain_created`.

### Analysis modules (live mode only)

- `DeepCodeAnalyser` — CMS, language, framework from HTML/headers
- `JSAnalyser` — external JS URLs, social links
- `SimpleSaver.save_parsing_results` — persists HTML + JSON to disk

### Disk mode

Loads `{company_name}.json` for cms/language/framework/js/social fields (does not re-run analyzers on HTML).

---

## WHOIS / IDN domains (`DomainWhois.py`)

1. Extract host from URL (`extract_domain_from_url`).
2. Try `python-whois` on punycode + original domain.
3. **Fallback for `.ru` / `.рф`**: `whois -h whois.tcinet.ru <punycode-domain>` and parse `created:` line.

Requirements:

- Package: `python-whois` (import `whois`).
- System binary: **`whois`** must be available for `.ru`/`.рф` fallback.
- Docker image currently does **not** install `whois`; add `apt-get install whois` if WHOIS is needed in containers.

Cyrillic domains (e.g. `южныйгазмаркет.рф`) are converted to punycode before lookup.

---

## API reference (`app.py`)

Interactive docs: `http://localhost:8000/docs`

Global DB handle: module-level `PostgresDB` instance `db` with long-lived `db.session`.

### Implemented endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/companies` | Create company (identity + URL only) |
| GET | `/companies` | List companies with **latest** `companies_data` fields |
| GET | `/companies/{city}/{industry}/{company_name}` | Single company (latest data) — **legacy path, marked for removal in README** |
| POST | `/companies/analyze` | Batch analyze (see below) |
| DELETE | `/companies/{id}/data/{data_id}` | Delete one data row (DB only) |
| DELETE | `/companies/{id}/data` | Delete all data rows for company (DB only) |
| DELETE | `/companies/{id}` | Delete company + all its data (DB only) |

### POST `/companies/analyze` body

```json
{
  "ids": [1, 2],
  "cities": ["Краснодар"],
  "industries": ["Насосное оборудование"],
  "date": "2024-12-27"
}
```

All fields optional / nullable. Filters combine with **AND**. Empty filters → all companies.

- Field name in Python model: `parse_date` with **`Field(alias="date")`** — do not name a Pydantic field `date` (shadows `datetime.date` and breaks schema generation).
- `date` set → disk mode; `date` null → live internet mode.

Response: `{ "results": [{ "id", "company_name", "city", "industry", "status", "detail" }] }`.

### POST `/companies` body

```json
{
  "city": "...",
  "industry": "...",
  "company_name": "...",
  "url": "https://..."
}
```

Duplicate check: same `(city, industry, company_name)` → 400.

---

## Database access patterns

### Preferred in new API code

Use SQLAlchemy directly on `db.session`:

```python
db.session.query(Company).filter(Company.id == id).first()
db.session.add(row)
db.session.commit()
db.session.rollback()  # on error
```

### Legacy `PostgresDB` helpers (still used)

| Method | Purpose |
|--------|---------|
| `get_company(city, industry, name)` | Returns tuple; analysis fields are always `None` |
| `get_company_by_id(id)` | Returns `Company` ORM object |
| `set("companies", (name, city, industry, url))` | Insert company |
| `set_field(...)` | Update one company column |

**Do not** use `db.get("companies")` for analysis fields — it only returns `(name, city, industry)`.

When changing models, update **`SqlORM.py`** and add an **Alembic migration**. Keep `alembic/env.py` imports in sync (`Base`, all models) for autogenerate.

### Migration chain (current)

```
001 → 410811fb2a19 → 0c09354fedd8 → f7e2a9b1c3d4 (domain_created)
```

Commands:

```bash
source venv/bin/activate
alembic upgrade head
# or
python run_migrations.py upgrade
```

After model changes:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## Environment variables

| Variable | Default | Used by |
|----------|---------|---------|
| `POSTGRES_DB` | `webanalysis` | API, Alembic |
| `POSTGRES_USER` | `exampleuser` | |
| `POSTGRES_PASSWORD` | `examplepwd` | |
| `POSTGRES_HOST` | `localhost` (API), `db` (Compose) | |
| `POSTGRES_PORT` | `5432` | |

---

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app:app --reload
```

**Requires venv** — bare `uvicorn` fails if not activated.

Live analyze requires:

- Network access
- Chrome + ChromeDriver (via `webdriver-manager`) for screenshots

Docker Compose:

```bash
docker-compose up
# API :8000, Adminer :8080, Postgres :5432
```

Compose runs `alembic upgrade head` before Uvicorn and mounts the repo at `/app`.

---

## CSV format (`companies.csv`)

Delimiter: **`;`**

```csv
industry;city;company_name;url
```

`Main.main()` reads this file to bulk-insert companies (analyze step is currently commented out).

---

## Coding conventions for agents

1. **Minimal diffs** — match existing style (mixed RU comments in older modules, EN in newer API code).
2. **Schema changes** — always Alembic migration + `SqlORM.py` model update together.
3. **Company name** — normalize with `.replace("/", "-")` before save/compare.
4. **Analysis fields** live on `companies_data`, not `companies`.
5. **DELETE endpoints** — DB only unless explicitly asked to touch `ParsedData/`.
6. **Pydantic** — avoid field names that shadow types (`date`, `id` as model attr with type annotation issues); use aliases where needed.
7. **FastAPI route order** — static paths like `/companies/analyze` must be registered before parameterized `/companies/{...}` if paths could overlap (numeric `id` routes are fine vs city-based GET).
8. **Do not commit** unless the user asks. Do not edit `README.md` / `AGENTS.md` unless asked.

---

## Known gotchas

| Issue | Detail |
|-------|--------|
| `db.get_company` tuple | Indices 4–8 are placeholder `None`; use `CompanyData` query for analysis fields |
| WHOIS in Docker | Install `whois` system package for `.ru`/`.рф` fallback |
| Selenium in CI/sandbox | Screenshot step fails without Chrome; live analyze returns error |
| `python-whois` socket errors | Expected for some TLDs; fallback or `None` domain_created is OK |
| Disk analyze | Folder must exist with both `.html` and `.json` |
| Re-analyze same calendar date | Upserts existing `companies_data` row for that `date_parse` |
| Live analyze same day twice | Creates **two** rows if run on different calendar days; same-day second run also inserts (no upsert in live mode) |
| `.gitignore` | `ParsedData/` and `/*.csv` ignored — do not assume CSV/ParsedData in git |
| `alembic/env.py` | Imports `Company` only; import `CompanyData` too when autogenerating |

---

## Planned work (from README TODO)

Not yet implemented — safe targets for future tasks:

- [ ] `GET /companies` filters (city, industry) and pagination
- [ ] Remove `GET /companies/{city}/{industry}/{company_name}`
- [ ] `GET /companies/{id}` — company fields + full ordered `companies_data` history
- [ ] `PATCH /companies/{id}` — update company fields

---

## Debugging checklist

1. DB reachable? `GET /health`, check Compose logs, `alembic current`.
2. Migration applied? `\d companies_data` should include `domain_created`.
3. Analyze fails for disk date? Verify `ParsedData/{industry}/{city}/{name}/{dd.mm.yyyy}/` exists.
4. Null fields on `GET /companies`? Confirm rows in `companies_data` and latest `date_parse`.
5. WHOIS null? Test `DomainWhois.get_domain_created_date(url)` in REPL; check `whois` CLI for `.рф`.
6. Import errors on startup? Activate venv; check for Pydantic field name shadowing (`date`).

---

## Quick test commands

```bash
# Import check
./venv/bin/python -c "import app; import Main"

# WHOIS smoke test
./venv/bin/python -c "from DomainWhois import get_domain_created_date; print(get_domain_created_date('https://example.com'))"

# Create company
curl -s -X POST http://127.0.0.1:8000/companies \
  -H 'Content-Type: application/json' \
  -d '{"city":"Краснодар","industry":"Test","company_name":"Demo","url":"https://example.com"}'

# Analyze by id (live)
curl -s -X POST http://127.0.0.1:8000/companies/analyze \
  -H 'Content-Type: application/json' \
  -d '{"ids":[1]}'
```
