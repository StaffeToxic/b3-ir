# Research — b3-ir MVP

Status: **OPEN**. Each front below is dispatched to one Maestri agent, which
writes `research/<front>.md`. Claude reads the reports, decides, and records
each decision here as Decision / Rationale / Alternatives. Until a decision is
recorded, every value in the front is `UNVERIFIED` and must not be implemented
as verified (Constitution I).

Report format required from agents, per item: value, legal source (law / IN /
article / paragraph, with official URL), validity dates, and `UNVERIFIED` when
the official text could not be confirmed. No secondary blogs as sole source.

## R1 — Spot-market tax rules for stocks and ETFs (2024–2026)

Swing and day-trade rates; IRRF on sales ("dedo-duro") and on day trade; the
monthly stock-sale exemption limit and whether it applies to ETFs; loss
offsetting between swing/day trade and across asset classes; minimum DARF and
carryover; DARF revenue code(s) and due date; trade date vs settlement date as
reference. Must check whether any 2025–2026 legislation (e.g. MP 1303/2025 and
its outcome, Lei 15.270/2025, later acts) changed these rules and from when.

## R2 — FII rules

Rate on FII quota sales, absence of exemption, loss offsetting (FII only?),
day trade on FIIs, tax on FII income distributions for individuals and conditions
for exemption; 2025–2026 changes.

## R3 — Average price, costs and corporate events

How brokerage costs, B3 fees and ISS enter acquisition cost and sale value;
proportional allocation within a note; split/reverse split treatment; bonus
shares cost (value attributed by the company, per IN RFB 1.585/2015 or current
norm); fractional shares from events.

## R4 — Inputs: SINACOR note layout and B3 Área do Investidor exports

SINACOR note sections and fields (trade lines, "Resumo dos Negócios", "Resumo
Financeiro", IRRF lines), known per-broker variations; current B3 Área do
Investidor export formats for Negociação and Movimentação (columns, event names
for splits, bonus, dividends, JCP, FII income); how to tell FII vs ETF vs stock
offline (B3 public lists, ticker suffix 11 ambiguity) and a license-compatible
source for a bundled ticker table.

## R5 — Annual return (DIRPF) mapping

Bens e Direitos group/code for stocks, FIIs and ETFs; Renda Variável monthly
sheet (operações comuns/day trade, FII sheet); Rendimentos Isentos lines for
exempt stock gains and dividends/FII income; Tributação Exclusiva for JCP;
treatment of dividends from 2026 onwards under Lei 15.270/2025.

## R6 — Prior art and port reference

Existing open-source projects for B3 IR (license, maintenance, gaps) to avoid
duplication and reuse test cases; inventory of MonnaIA (TypeScript, private
repo `StaffeToxic/MonnaIA`) modules for average price, parsing and assessment,
with the test cases worth porting.

## Decisions

_None yet._
