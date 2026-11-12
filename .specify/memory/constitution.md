<!--
Sync Impact Report
- Version: (template) → 1.0.0 (initial ratification)
- Principles added: I–VII (all new)
- Sections added: Technical Constraints, Development Workflow, Governance
- Templates: .specify/templates/tasks-template.md marks tests as OPTIONAL; this
  constitution overrides it (Principle III). Template NOT edited on purpose
  (Spec Kit overwrites templates on upgrade); this report is the source of truth.
- Deferred TODOs: none
-->

# b3-ir Constitution

## Core Principles

### I. Every tax rule has a cited legal source (NON-NEGOTIABLE)

Every tax rule implemented (rates, exemption limits, loss offsetting, day-trade
classification, withholding, DARF codes, due dates) MUST cite its legal source
(law, Receita Federal normative instruction, article/paragraph) in the code
docstring and in `docs/regras-fiscais.md`. A rule without a confirmed source is
not implemented: the library raises `UnsupportedOperationError` (or flags the
item as `UNVERIFIED` in reports) instead of guessing. Plausible values are never
invented.

Rationale: users file taxes with these numbers. A silent wrong answer is worse
than an explicit "not supported".

### II. Money is exact (NON-NEGOTIABLE)

Monetary values and quantities use `decimal.Decimal`, never `float`. Rounding
happens only at documented points, with the rounding mode stated next to the
rule source. Every amount carries its currency implicitly as BRL; no mixing.

### III. Test-first with hand-checked cases (NON-NEGOTIABLE)

Each tax rule ships with tests built from hand-computed examples (expected
values written in the test, with the calculation in a comment). Parsers ship
with anonymized fixtures. Tests are written before or with the implementation,
never "later". The `tasks-template.md` note that tests are optional does NOT
apply to this project.

### IV. Privacy by default (NON-NEGOTIABLE)

All processing is local. No network calls, telemetry, or uploads at runtime.
No real user document (brokerage note, B3 statement) is ever committed: fixtures
are synthetic or fully anonymized (no CPF, account number, name, or real
broker client code). Logs never print CPF or account numbers.

### V. Library-first, thin CLI

The domain core (positions, average price, monthly assessment, DARF, annual
report data) is pure Python with no I/O. Input adapters (PDF/XLSX parsers) and
output adapters (CLI, JSON, CSV) depend on the core, never the reverse. The CLI
supports human-readable and JSON output; errors go to stderr with non-zero
exit codes.

### VI. Honest scope

The tool states clearly what it does not support (asset classes, events,
brokers) and refuses those inputs explicitly. README and CLI output carry the
disclaimer that this is not tax advice and that the user is responsible for
their filing.

### VII. Simplicity

Minimal dependencies, each justified in `plan.md`. No speculative abstractions
(plugin systems, multi-country support, databases) until a real need appears.

## Technical Constraints

- Python >= 3.11, packaged with `pyproject.toml`, distributed on PyPI as `b3-ir`.
- Code, identifiers, comments, commits, and PRs in English. User-facing docs
  (README, `docs/`) and CLI messages in Brazilian Portuguese, since the audience
  is Brazilian investors.
- License: MIT.
- Quality gates: `pytest` green, `ruff` clean, type-checked with `mypy --strict`
  on the core package.

## Development Workflow

- Work on task branches, never directly on `main`. Conventional Commits.
- Authorship: every commit has the repository owner (Anthony Oliveira
  <staffetoxic@gmail.com>) as author and committer. No `Co-Authored-By` lines and
  no AI attribution in commits, PR titles, or PR bodies.
- Agents may commit on their task branch. Push, merge into `main`, release, and
  PyPI publication require explicit authorization from the owner.
- Irreversible operations (force push, history rewrite, remote deletion) require
  explicit confirmation.
- "Done" means: acceptance criteria checked, tests and gates executed, and the
  output shown. Anything not confirmed is reported as `UNVERIFIED`.

## Governance

Precedence: direct instruction from the owner > this constitution > feature
artifacts (`specs/NNN/`) > tool templates and defaults.

Amendments update this file with a version bump (semantic versioning: MAJOR for
removed/redefined principles, MINOR for added ones, PATCH for wording) and a new
Sync Impact Report. Every review checks compliance with the NON-NEGOTIABLE
principles before merge.

**Version**: 1.0.0 | **Ratified**: 2026-11-11 | **Last Amended**: 2026-11-11
