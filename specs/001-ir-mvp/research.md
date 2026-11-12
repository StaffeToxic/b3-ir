# Research — b3-ir MVP

Status: **all fronts (R1-R6) decided (2026-11-11).** Each front below is dispatched to one Maestri agent, which
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

### D-R6-1 — Corporate events carry a signed quantity delta

- **Decision**: `CorporateEvent.quantity_delta` (signed) replaces `ratio`.
- **Rationale**: B3 Movimentação reports splits/reverse splits/bonus as shares
  credited or debited, not as a factor (MonnaIA `positions.ts`). Using the delta
  avoids recomputing a ratio and rounding fractional shares.
- **Alternatives**: keep `ratio` and derive it from the delta (rejected: lossy when
  fractions are auctioned).

### D-R6-2 — Oversold positions are refused

- **Decision**: a sale larger than the position raises `UnsupportedOperationError`.
- **Rationale**: Constitution VI; MonnaIA clamps to zero, which hides missing data.
- **Alternatives**: clamp (rejected), allow short positions (out of MVP scope).

### D-R1-1 — Rates, limits and codes confirmed in official texts

- **Decision**: mark as verified in `rules.py`: 15% common (Lei 11.033 art. 2 II),
  20% day trade (art. 2 I), 20% FII (Lei 8.668 art. 18), R$ 20,000 stock-sale
  exemption (Lei 11.033 art. 3 I; IN 1.585 art. 59), IRRF 0.005% (Lei 11.033 art. 2
  par. 1 IV) and 1% day trade (Lei 9.959 art. 8), R$ 10 minimum DARF (Lei 9.430
  art. 68), code 6015 (RFB Agenda Tributaria), due on the last business day of the
  next month (IN 1.585 art. 56 par. 5). Texts versioned in `legislacao/`.
- **Rationale**: Constitution I. Downloaded from Planalto and the RFB normative API;
  SHA-256 in each file's front matter.
- **Alternatives**: secondary sources (blogs, broker FAQs) rejected as sole source.

### D-R1-2 — Day trade is per broker

- **Decision**: `Operation.broker` added; day trade pairs only same day, same
  ticker, same broker, in trade order (Lei 9.959 art. 8 par. 1 I a, wording of Lei
  12.350/2010; IN 1.585 art. 65 pars. 1-3). Manual CSV gets an optional `corretora`
  column; without it, all operations of the day are treated as one broker.
- **Rationale**: grouping only by day and ticker misclassified trades at two brokers.

### D-R1-3 — IRRF balance closes at year end

- **Decision**: unused IRRF carries across months but not across years; the leftover
  is reported on the last month of the year.
- **Rationale**: 0.005% balance goes to the annual return (Lei 11.033 art. 2 par. 7
  III); day-trade balance only by refund request (IN 1.585 art. 65 par. 9).

### D-R1-4 — Exemption sum uses swing stock sales only

- **Decision**: the R$ 20,000 test sums stock sales in common operations.
- **Rationale**: IN 1.585 art. 59 par. 2 I excludes day trade from the exemption;
  the text does not say whether day-trade sales count toward the sum, so this is
  documented as an interpretation in `docs/regras-fiscais.md`, not hidden.

### D-R1-5 — 2025-2026 changes

- **Decision**: no change to the monthly rules. MP 1.303/2025 shows "Vigencia
  encerrada" in every compiled text. Lei 15.270/2025 (10% withholding on dividends
  above R$ 50,000 per month from the same company, from 2026) goes to R5 (annual report).

### D-R1-6 — Rounding stays UNVERIFIED but only flags when it matters

- **Decision**: no official source found for the rounding mode of the DARF amount;
  the month is flagged only when rounding actually changes the value.

### D-R6-3 — Prior art: COIR and correpy

- **Findings** (GitHub search, 2026-11-11):
  - `MarceloPCF/COIR` (AGPL-3.0, active): Windows desktop app that already does
    SINACOR notes, B3 statements, options, futures, DARF with penalties and DIRPF.
  - `thiagosalvatore/correpy` (Apache-2.0, PyPI, last push 2024-08): SINACOR PDF
    parser library, no tax logic.
  - Others are small or stale (<20 stars).
- **Decision**: b3-ir positions itself as a **library + cross-platform CLI** under MIT,
  with every rule traceable to versioned legal texts; it does not try to be a
  desktop app. For R4, evaluate depending on `correpy` for SINACOR parsing
  (license-compatible) before writing a parser from scratch.

### D-R4-1 — SINACOR notes via correpy, as an optional extra

- **Decision**: read PDF notes with `correpy` (Apache-2.0) behind the `b3-ir[pdf]`
  extra, imported lazily. b3-ir takes trades, fees and the note's IRRF line;
  correpy's per-trade IRRF estimate (computed from a float) is ignored, fees are
  allocated by value (IN 1.585 art. 56 par. 4) and the note IRRF by sale value.
  A note with any out-of-scope item is refused whole, since its fees cover all items.
  The PDF's parent folder name is the broker (correpy does not expose it).
- **Rationale**: correpy depends on PyMuPDF (AGPL-3.0 or commercial). A hard
  dependency would pass AGPL obligations to every b3-ir user; as an extra, the core
  stays MIT-only and users opt in. CI runs without it (tests use fakes).
- **Evidence**: on correpy's sample note (2022, 17 trades) fees 9.50 allocate
  exactly and the note IRRF 0.79 equals 0.005% of the R$ 15,801.54 sold.
- **Alternatives**: own parser on pdfplumber (MIT; more work, no layout corpus);
  hard dependency on correpy (rejected: AGPL leak).

### D-R4-2 — Bundled asset catalog from COTAHIST

- **Decision**: `src/b3_ir/data/ativos.csv` built from B3 COTAHIST 2022-2026
  (`scripts/atualizar_ativos.py`): every (ticker, class, trading name,
  specification). BDI 02/07/08 = stock, 12 = FII, 14 = ETF; BDRs (BDI 34-36 or
  DR* specification), rights, Fiagro and fractional lots are excluded, so they are
  refused downstream. Event marks (EJ, ED, ATZ, CI...) are stripped on both sides.
- **Rationale**: real notes print "BBSEGURIDADE ON NM", not BBSE3; correpy's regex
  finds no ticker in 17 of 17 trades of its own sample. The catalog resolves all 17.
  It also replaces the *11 heuristic (FII vs ETF vs unit) for known tickers.
- **Limits**: names not quoted since 2022 or shared by several tickers (e.g.
  "FII KINEA") are refused, never guessed; rerun the script with more years.

### D-R4-3 — B3 statements: trades from Negociação, events and income from Movimentação

- **Decision**: `parsers/b3_statements.py` detects the statement by its header.
  Negociação gives operations (trade date, broker = "Instituição", zero costs plus a
  warning). Movimentação gives splits, reverse splits, bonus shares and income
  (dividends, JCP, FII income); "Transferência - Liquidação" rows are ignored and
  any other label is listed as unsupported. Trades in both a note/CSV and the
  statement are deduplicated by (date, ticker, side, quantity, price), counting
  repeats; the note copy wins because it has costs and IRRF.
- **Rationale**: Movimentação lists trades by settlement date (D+2), which would
  move trades across months and break day-trade pairing. Bonus shares without the
  cost per share in the statement are refused (IN 1.585 art. 58 par. 1 needs it).
- **UNVERIFIED**: the Negociação column names come from memory of the export, not
  from an official layout; Movimentação labels come from MonnaIA's catalog of real
  exports. Header matching is alias-based and accent-insensitive; both need a test
  against a real export before release.

### D-R5-1 — Annual report: field names, not form codes

- **Decision**: `domain/annual.py` reports assets at 31/12 of the previous and current
  year (acquisition cost), the monthly table, exempt income (stock gains under the
  R$ 20,000 limit, dividends, FII income) and exclusive taxation (JCP), naming each
  DIRPF field instead of printing its group/code or income-type number. Assets bought
  and sold within the year are not listed (held on neither 31/12).
- **Sources**: Lei 11.033 art. 3 I and III (+ par. 1: FII exemption needs >= 100
  holders and < 10% of quotas; reported as a warning, not checkable offline); Lei
  9.249 art. 10 (dividends) and art. 9 par. 2 (JCP withholding); RFB "Perguntas e
  Respostas IRPF 2026" v1.00 of 2026-04-23 (q. 320, 707-710; SHA-256
  f3740385c07fa4dc52f8614d009dd5bd038fbeb8bd935f89da4e9bc26ed2a3b0).
- **Rationale**: the Q&A and the laws do not give the form codes; they are set by
  each year's DIRPF program. Printing unverified codes would look authoritative.

### D-R5-2 — JCP rate changes in 2026; dividend withholding from 2026

- **Decision**: `jcp_withholding_rate` has two versions: 15% until 2025-12-31 and
  17.5% from 2026-01-01 (LC 224/2025 art. 8, effects art. 14 III, amending Lei 9.249
  art. 9 par. 2). Dividends above R$ 50,000 per month from the same company have 10%
  withholding from 2026 (Lei 9.250 art. 6-A, by Lei 15.270/2025): reported as a
  warning per ticker and month (a company with several tickers is summed per ticker,
  so the warning says the limit is per company).
- **Finding**: the RFB Q&A 2026 (year 2025) still says 15%, which is right for 2025;
  the compiled Lei 9.249 shows 17.5%. The registry's validity dates resolve both.
