# Tasks — b3-ir MVP

Tests are mandatory for every implementation ticket (Constitution III overrides
the template). Each ticket: one branch `001-ir-mvp/<ticket-id>`, commits by the
owner identity only, no AI attribution. Status lives in the Maestri canvas note
`TICKET-<id>`; this file is requirements and traceability.

Legend: `blockedBy` = real dependency; `conflictKeys` = paths that cannot be edited
by two tickets at once; risk `high` = tax correctness.

## Wave 0 — Research (read-only, parallel)

| ID | Ticket | blockedBy | conflictKeys | Output |
|---|---|---|---|---|
| R1 | Stocks/ETF tax rules | — | — | `research/r1-acoes-etf.md` |
| R2 | FII rules | — | — | `research/r2-fii.md` |
| R3 | Average price, costs, events | — | — | `research/r3-preco-medio.md` |
| R4 | SINACOR + B3 export formats, ticker table | — | — | `research/r4-entradas.md` |
| R5 | DIRPF mapping | — | — | `research/r5-dirpf.md` |
| R6 | Prior art + MonnaIA inventory | — | — | `research/r6-prior-art.md` |
| D0 | Claude consolidates decisions in `research.md` | R1–R6 | research.md | decisions |

## Wave 1 — Foundation

| ID | Ticket | blockedBy | conflictKeys | Risk | Accept |
|---|---|---|---|---|---|
| T001 | Scaffold: `pyproject.toml` (hatchling, src layout, entry point `b3-ir`), ruff/mypy config, pytest, GitHub Actions CI matrix 3.11–3.13 × ubuntu/windows/macos, MIT LICENSE, README stub with disclaimer | — | pyproject.toml, .github/ | low | `pip install -e .[dev]`, `pytest`, `ruff check`, `mypy` pass on empty package |
| T002 | `errors.py`, `money.py`, `domain/models.py` per `contracts/domain-api.md` | T001 | src/b3_ir/domain/models.py | low | unit tests for invariants (non-negative qty, Decimal-only) |
| T003 | `rules.py` registry + `docs/regras-fiscais.md` with every rule from D0; test that each rule has source, and that unverified rules flag | T001, D0 | src/b3_ir/rules.py, docs/regras-fiscais.md | high | registry test green; every R1/R2/R3/R5 decision present |
| T004 | Architecture tests: domain has no I/O/network imports; no `float` in domain | T002 | tests/test_architecture.py | low | test green |
| T005 | Synthetic fixtures generator (SINACOR-like PDFs + B3 XLSX) and one golden year scenario with hand-computed expected values documented | T002, D0 | tests/fixtures/, tests/golden/ | high | fixtures regenerate deterministically; no personal data |

## Wave 2 — Domain core

| ID | Ticket | blockedBy | conflictKeys | Risk |
|---|---|---|---|---|
| T010 | `classify.py`: asset class via bundled ticker table + day/swing classification | T002, T003 | src/b3_ir/domain/classify.py, src/b3_ir/data/ | high |
| T011 | `costs.py`: proportional note cost allocation | T002, T003 | src/b3_ir/domain/costs.py | high |
| T012 | `positions.py`: average price engine + split/reverse split/bonus + short-sale refusal | T002, T003, T011 | src/b3_ir/domain/positions.py | high |
| T013 | `assessment.py`: monthly results per category, exemption, loss balances, IRRF, minimum DARF carryover, DARF data | T010, T012, T005 | src/b3_ir/domain/assessment.py | high |
| T014 | `annual.py`: annual report data | T012, T013 | src/b3_ir/domain/annual.py | high |

## Wave 3 — Adapters

| ID | Ticket | blockedBy | conflictKeys | Risk |
|---|---|---|---|---|
| T020 | `parsers/sinacor.py` against fixtures | T002, T005 | src/b3_ir/parsers/sinacor.py | medium |
| T021 | `parsers/b3_statements.py` against fixtures | T002, T005 | src/b3_ir/parsers/b3_statements.py | medium |
| T022 | `parsers/dedup.py` | T020, T021 | src/b3_ir/parsers/dedup.py | medium |
| T023 | `report/` text, JSON, CSV per `contracts/cli.md` | T013, T014 | src/b3_ir/report/ | low |
| T025 | `parsers/csv_ops.py` manual CSV (FR-015) | T002 | src/b3_ir/parsers/csv_ops.py | low |
| T024 | `cli.py` commands, exit codes, disclaimer | T022, T023 | src/b3_ir/cli.py | low |

## Wave 4 — Release readiness

| ID | Ticket | blockedBy | conflictKeys | Risk |
|---|---|---|---|---|
| T030 | End-to-end golden test via CLI on fixture year (SC-001, SC-004) + performance test 300 notes (SC-005) | T024 | tests/golden/ | high |
| T031 | README pt-BR (install, usage, scope, disclaimer), CONTRIBUTING, CHANGELOG, CITATION.cff | T024 | README.md, docs/ | low |
| T032 | Build sdist/wheel + `twine check`; release workflow (Trusted Publishing) prepared but NOT run | T030, T031 | .github/workflows/release.yml | medium |

Publication to PyPI and GitHub release: owner authorization only.

## Ready-set rules

Max 3 tickets in parallel and 1 `high` at a time. Wave 1 ready-set after D0:
T001 → then {T002}; after T002: {T003, T004, T005} with only one `high`
(T003 first, then T005). Within Wave 2, T010 and T011 run in parallel (disjoint
files) but both `high`, so serialize. Review of each ticket by a second agent
before integration.

## Traceability

FR-001 T020 · FR-002 T011 · FR-003 T021 · FR-004 T022 · FR-005 T010 · FR-006 T010 ·
FR-007 T012 · FR-008 T013 · FR-009 T013 · FR-010 T014 · FR-011 T023/T024 ·
FR-012 T003 · FR-013 T004 · FR-014 T024/T031 · FR-015 T025 · SC-001 T030 · SC-002 T003 ·
SC-003 T031/T032 · SC-004 T030 · SC-005 T030 · SC-006 T005
