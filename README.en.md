# Acervo

[Español](README.md) · **English**

A system to **retrieve and validate documents with full provenance**. It has two modes that
share a single Downloader:

- **Legal mode (LegisUni):** given the name of a Mexican public university, it locates the
  official sources, extracts the full catalog of the university's regulations, cross-checks that
  the catalog is complete, downloads the documents, and verifies that they are authentic, in
  force, and intact. The output is a regulatory corpus ready for a downstream RAG system.
- **Academic mode:** given a list of scientific articles (references, DOIs, or links, in a
  `.docx`), it downloads whatever open-access copies it can find, verifies that each file is the
  requested article, and reports what it got, what it didn't, and why.

**What it is not:** it is not a literature search engine (the user brings the list), it does not
bypass paywalls, and it does not index documents or answer legal questions. It only retrieves
and validates documents.

> The Python package is called `legisuni` for historical reasons. The system's name is
> **Acervo**.

> **Language note:** this README is the only English document. The specification in `docs/`,
> the code identifiers, and the commit messages are in Spanish. A short glossary is at the end.

---

## Status

*As of 2026-11-23, micro-task M50.*

| Component | Mode | Status |
|---|---|---|
| ④ Downloader (*Descargador*) | shared | **Done.** Migrated to `Encargo`; two real legal runs and one academic run. Tags `descargador-v1-cerrado` → `descargador-v2-reparado`. |
| ② Index Reader (*Lector de índice*) | legal | **In progress.** Deterministic core done (M41–M48); `Catalog`, agent output and mock agent (M49); evaluation-artifact recorder (M50). The real agent is pending. |
| ⑤ Document Verifier (*Verificador documental*) | legal | Specified, no code yet. |
| ③ Corroborator (*Corroborador*) | legal | Specified, no code yet. |
| ① Locator (*Localizador*) | legal | Specified, no code yet. |
| Orchestration, persistence, and the `acervo` CLI | both | Specified, no code yet. Today the system is driven by the scripts in `scripts/`. |
| List Reader, Text Extraction (OCR), Academic Verifier, Batch Auditor | academic / shared | Not yet specified. |

Live details are in [`docs/PLAN-MIGRACION.md`](docs/PLAN-MIGRACION.md) and in the version header
of each document in `docs/`.

---

## Documentation

The specification lives in [`docs/`](docs/) (in Spanish). Read it in this order:

| File | What it is |
|---|---|
| [`00-VISION-Y-ARQUITECTURA.md`](docs/00-VISION-Y-ARQUITECTURA.md) | Vision and architecture: what is being built, why agents, design decisions (D1–D15). |
| [`01-CONTRATOS-DE-DATOS.md`](docs/01-CONTRATOS-DE-DATOS.md) | Data contracts N0–N15. **Binding:** the only boundary between components. |
| [`02-SPEC-LOCALIZADOR.md`](docs/02-SPEC-LOCALIZADOR.md) | ① Locator (legal). |
| [`03-SPEC-LECTOR-DE-INDICE.md`](docs/03-SPEC-LECTOR-DE-INDICE.md) | ② Index Reader (legal). |
| [`04-SPEC-CORROBORADOR.md`](docs/04-SPEC-CORROBORADOR.md) | ③ Corroborator (legal). |
| [`05-SPEC-DESCARGADOR.md`](docs/05-SPEC-DESCARGADOR.md) | ④ Downloader (shared). |
| [`06-SPEC-VERIFICADOR-DOCUMENTAL.md`](docs/06-SPEC-VERIFICADOR-DOCUMENTAL.md) | ⑤ Document Verifier (legal). |
| [`07-SPEC-ORQUESTACION-PERSISTENCIA-Y-CLI.md`](docs/07-SPEC-ORQUESTACION-PERSISTENCIA-Y-CLI.md) | Flows, single database, and the `acervo` CLI. |
| [`08-EVIDENCIA-DE-CAMPO.md`](docs/08-EVIDENCIA-DE-CAMPO.md) | Field evidence (UAM, UNAM, UJAT, UACAM) and real runs. |
| [`PLAN-MIGRACION.md`](docs/PLAN-MIGRACION.md) | Micro-tasks, one per commit. |

---

## Repository layout

```
legisuni/
  contracts/     Pydantic schemas from docs/01 (N0–N15)
  descargador/   Component ④: HTTP client, robots.txt, walls, landing pages, SQLite store
  lector/        Component ②: deterministic index extraction, Catalog assembly
  juridico/      CatalogEntry → Encargo translation
  datos/         Packaged patterns and configuration tables
  config.py      Settings (LEGISUNI_* variables)
scripts/         Run and repair scripts; not part of the package
tests/           Tests with no network and no real disk access
datos/           Input batches of download requests (encargos)
fixtures/        Real HTML captured from institutional index pages
docs/            Specification
```

---

## Installation

Requires Python 3.12 or later.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env   # then fill in the values
```

Configuration is read from `LEGISUNI_*` variables (see [`.env.example`](.env.example)): LLM API
key, model, User-Agent, data root, database path, and timeout, size, and rate limits.

## Tests

```bash
.venv/bin/python -m pytest -q
```

Tests do not touch the network or the real disk.

## Usage

Until the `acervo` CLI exists, the system is driven by scripts:

```bash
# Legal mode: extract a saved index page, no network and no database
.venv/bin/python scripts/cosechar_indice.py \
  --html fixtures/uam-index.html \
  --url-indice https://www.uam.mx/legislacion/index.html \
  --inst-id uam --solo-extraer

# Academic mode: show what a batch would download, without downloading
.venv/bin/python scripts/lote.py --encargos datos/encargos_bloque_a.json --dry-run
```

> ⚠️ **Without `--solo-extraer` or `--dry-run`, these scripts send real requests to university
> servers.** They honor `robots.txt` and a per-domain rate limit, but use them with care.

---

## Working method

- The contracts in `docs/01` are not changed without an explicit decision.
- Work proceeds in small micro-tasks defined in `docs/PLAN-MIGRACION.md`, one per commit
  (`MN: description`).
- No migration changes an existing behavioral assertion.
- Measured facts are kept apart from assumptions: if it is not in `docs/08`, it is an assumption.

## Sibling project

Acervo is a separate system from `RAG_publish`: it shares no code, contracts, or database. It
shares the working method and a destination: the legal-mode corpus will feed a legal RAG system
to be specified elsewhere.

---

## Glossary

| Spanish | English |
|---|---|
| Acervo | Collection / holdings |
| Encargo | Download request (one item to fetch) |
| Descargador | Downloader |
| Lector de índice | Index Reader |
| Corroborador | Corroborator |
| Verificador documental | Document Verifier |
| Localizador | Locator |
| Lote | Batch |
| Muro (de pago) | Paywall or institutional login; detected, never bypassed |
| Vestíbulo | HTML landing page that links to the actual file |
| Normativa / legislación universitaria | University regulations |
| Contratos de datos | Data contracts |
| Evidencia de campo | Field evidence |
