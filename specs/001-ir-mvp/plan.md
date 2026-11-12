# Implementation Plan: b3-ir MVP

**Branch**: `001-ir-mvp` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

## Summary

Python library + CLI that turns B3 brokerage notes (SINACOR PDF) and Área do
Investidor statements into normalized operations, computes positions/average
price, monthly IR assessment with DARF data, and annual return data, for stocks,
FIIs and ETFs. Tax constants live in a single cited rules registry; anything not
confirmed by research is flagged `UNVERIFIED` or refused.

## Technical Context

**Language/Version**: Python >= 3.11
**Primary Dependencies**: `pdfplumber` (PDF text extraction, MIT), `openpyxl`
(B3 XLSX statements, MIT). CLI on stdlib `argparse` (Constitution VII: no Typer/Click).
**Dev Dependencies**: `pytest`, `pytest-cov`, `ruff`, `mypy`, `build`, `twine`
**Storage**: none (stateless; inputs are files, outputs go to stdout or `--saida`)
**Testing**: pytest; golden tests with hand-computed values; synthetic fixtures
**Target Platform**: Linux, macOS, Windows (CI matrix on GitHub Actions)
**Project Type**: single library + CLI
**Performance Goals**: 300 notes/year in < 30 s (SC-005)
**Constraints**: no network, `Decimal` only, no real personal data in repo
**Scale/Scope**: individual investor, one CPF, one or more brokers

## Constitution Check

| Principle | How the plan complies | Gate |
|---|---|---|
| I. Cited rules | All constants in `b3_ir/rules.py` registry with `source`; `docs/regras-fiscais.md` mirrors it; test `test_rules_registry.py` fails if a rule has no source or is unused | PASS (enforced by T003) |
| II. Exact money | `Decimal` everywhere; `ruff` rule bans `float(` in `src/b3_ir/domain`; rounding helpers in one module | PASS |
| III. Test-first | Every domain ticket starts with golden tests; DAG puts fixtures before logic | PASS |
| IV. Privacy | No network imports (test asserts `socket`/`urllib`/`requests` absent); fixtures synthetic | PASS |
| V. Library-first | `domain/` has no I/O imports (import-linter-style test) | PASS |
| VI. Honest scope | `UnsupportedOperationError`; reports carry `incomplete` flags; disclaimer in CLI | PASS |
| VII. Simplicity | 2 runtime deps; no DB, no plugin system | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-ir-mvp/
├── spec.md
├── plan.md              # this file
├── research.md          # decisions consolidated by Claude
├── research/            # one report per research front (written by agents)
├── contracts/
│   ├── cli.md
│   └── domain-api.md
└── tasks.md             # tickets + DAG
```

### Source Code (repository root)

```text
src/b3_ir/
├── __init__.py          # public API re-exports, __version__
├── errors.py            # B3IRError, ParseError, UnsupportedOperationError
├── money.py             # Decimal helpers, quantize/rounding (cited)
├── rules.py             # Rule registry: id, value, source, valid_from/to, verified
├── domain/
│   ├── models.py        # frozen dataclasses: Operation, CorporateEvent, IncomeEntry,
│   │                    # Position, MonthlyAssessment, Darf, AnnualReport
│   ├── classify.py      # asset class (stock/FII/ETF) + day/swing trade
│   ├── costs.py         # note cost allocation
│   ├── positions.py     # average price engine + corporate events
│   ├── assessment.py    # monthly assessment, exemption, losses, IRRF, DARF
│   └── annual.py        # annual return data
├── parsers/
│   ├── sinacor.py       # PDF note -> NoteParseResult
│   ├── b3_statements.py # XLSX trading/movement -> operations, events, income
│   └── dedup.py         # cross-source deduplication
├── report/
│   ├── text.py
│   ├── json_out.py
│   └── csv_out.py
└── cli.py               # argparse entry point `b3-ir`
tests/
├── unit/ ...            # mirrors src
├── golden/              # full-year scenarios with expected outputs
└── fixtures/            # synthetic notes/statements + generator script
docs/
└── regras-fiscais.md    # human-readable rules with legal sources
```

**Structure Decision**: single `src/` layout package (`b3_ir`), domain isolated
from parsers and reports, matching Constitution V. Asset-class lookup for FII vs
ETF vs stock uses a bundled static ticker table plus suffix heuristics, refreshed
manually (no network at runtime, Constitution IV); exact source decided in research R4.

## Contracts

Fixed before implementation; see `contracts/cli.md` and `contracts/domain-api.md`.

## Complexity Tracking

No violations.
