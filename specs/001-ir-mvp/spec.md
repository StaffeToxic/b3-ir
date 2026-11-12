# Feature Specification: b3-ir MVP — IR calculation for B3 stocks, FIIs and ETFs

**Feature Branch**: `001-ir-mvp`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "b3-ir: open-source Python library and CLI that reads B3 brokerage notes (PDF) and Área do Investidor statements, computes average price, monthly assessment, DARF, day trade and the R$20k exemption, and produces the data for the annual tax return. MVP covers stocks, FIIs and ETFs on the spot market."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monthly tax due from my trades (Priority: P1)

An individual investor points the CLI at a folder with their brokerage notes for a
year and gets, for each month, the net gain or loss per category (stocks swing
trade, stocks day trade, FIIs, ETFs), whether the stock exemption applied, the
accumulated losses carried forward, and the tax due with the DARF data (code,
due date, amount).

**Why this priority**: It is the monthly obligation every active investor has and
the main reason people pay for commercial tools. On its own it is a usable product.

**Independent Test**: Run the CLI on the synthetic fixture set (notes for one year
with known hand-computed results) and compare the monthly report with the
expected values in the test.

**Acceptance Scenarios**:

1. **Given** notes where a month has only stock swing-trade sales whose total
   sales value is under the exemption limit, **When** the user runs the monthly
   report, **Then** the month shows the gain as exempt and no DARF.
2. **Given** a month with stock sales above the exemption limit and a loss carried
   from a previous month, **When** the report runs, **Then** the loss is offset
   against the gain before computing the tax, and the remaining loss balance is shown.
3. **Given** a buy and a sale of the same ticker on the same day in the same
   note, **When** the report runs, **Then** the matched quantity is classified as
   day trade, taxed under day-trade rules, and its losses are kept in a separate
   balance from swing trade.
4. **Given** a month whose tax due is below the minimum DARF amount, **When** the
   report runs, **Then** no DARF is issued for that month and the amount is
   carried to the next month.
5. **Given** sales with withholding (IRRF) shown on the note, **When** the report
   runs, **Then** the withheld amount is deducted from the tax due.

---

### User Story 2 - Correct average price and positions (Priority: P1)

The investor sees, for each ticker, the current quantity and average acquisition
cost (including brokerage costs and fees from the notes), and how each buy, sale
and corporate event changed it.

**Why this priority**: Every gain and the annual return depend on the average
price; it is the core that US1 and US3 consume.

**Independent Test**: Feed a sequence of buys, sales and a split for one ticker
and check quantity and average price after each step against hand-computed values.

**Acceptance Scenarios**:

1. **Given** two buys of the same ticker at different prices with costs, **When**
   positions are computed, **Then** the average price is the weighted average
   including the costs allocated to each buy.
2. **Given** a sale, **When** positions are computed, **Then** the average price
   does not change and the realized gain uses it.
3. **Given** a split, reverse split or bonus share event, **When** positions are
   computed, **Then** quantity and average price are adjusted per the rule cited
   in `docs/regras-fiscais.md`.
4. **Given** a sale of more shares than the position holds (short sale), **When**
   positions are computed, **Then** the tool stops with an explicit "not supported"
   error naming the ticker and date.

---

### User Story 3 - Data for the annual tax return (Priority: P2)

At filing season the investor runs one command for a calendar year and gets the
data to fill the return: assets and rights at 31/12 (ticker, quantity, cost),
the monthly variable-income table (common/day trade and FII sections), exempt
income, and income subject to exclusive taxation, as text and as JSON/CSV.

**Why this priority**: Once a year but high-stakes; depends on US1 and US2.

**Independent Test**: For the synthetic fixture year, compare the generated report
with the expected values written in the test.

**Acceptance Scenarios**:

1. **Given** positions open on 31/12, **When** the annual report runs, **Then**
   each appears with quantity and total acquisition cost.
2. **Given** months with exempt stock gains, **When** the annual report runs,
   **Then** their sum appears under exempt income.
3. **Given** dividends and JCP from the Área do Investidor statement, **When** the
   annual report runs, **Then** they appear under the correct section per the
   cited rule.

---

### User Story 4 - Import from B3 Área do Investidor (Priority: P2)

The investor who does not have all PDF notes imports the trading and movement
statements exported from the B3 Área do Investidor, and the tool uses them for
trades, corporate events and income.

**Why this priority**: Many investors lose notes; B3 statements are the fallback
and the only source for events and income.

**Independent Test**: Import synthetic statement files and verify the normalized
operations, events and income match the expected list.

**Acceptance Scenarios**:

1. **Given** a trading statement, **When** imported, **Then** each row becomes a
   normalized buy/sale with date, ticker, quantity and price.
2. **Given** a movement statement with splits, bonus shares, dividends and JCP,
   **When** imported, **Then** they become normalized events and income entries.
3. **Given** the same trade present in both a note and a statement, **When** both
   are imported, **Then** it is counted once and the tool reports the duplicate.

### Edge Cases

- A note from an unsupported broker layout or a scanned (image-only) PDF: explicit
  error naming the file; other files keep processing.
- Notes containing options, futures, BDRs or other non-MVP instruments: those lines
  are reported as unsupported; the month is flagged as incomplete, never silently
  computed.
- A sale that makes the position negative (short selling): explicit "not supported".
- Ticker changes and mergers/spin-offs (not in MVP): flagged as unsupported events.
- A month where day-trade and swing-trade operations happen on the same ticker.
- Losses across categories: stock losses must not offset FII gains if the cited
  rule forbids it, and day-trade losses stay separate.
- Year boundaries: losses carried across years; trades on the last business day of
  December settled in January (trade date is the reference, per cited rule).
- Rules changed by recent legislation (2025–2026): if the effective rule for a date
  cannot be confirmed, the affected values are flagged `UNVERIFIED`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse brokerage notes in the SINACOR layout (PDF with
  text layer) into normalized operations: trade date, settlement date, ticker,
  side, quantity, unit price, and the note's costs and IRRF.
- **FR-002**: System MUST allocate note-level costs to each operation
  proportionally to its value, per the cited rule.
- **FR-003**: System MUST import B3 Área do Investidor trading and movement
  statements into normalized operations, corporate events and income entries.
- **FR-004**: System MUST deduplicate operations present in more than one source
  and report what was deduplicated.
- **FR-005**: System MUST classify each operation's asset as stock, FII or ETF;
  anything else is reported as unsupported.
- **FR-006**: System MUST classify day trade vs swing trade per the cited rule.
- **FR-007**: System MUST maintain per-ticker position and average price, applying
  splits, reverse splits and bonus shares.
- **FR-008**: System MUST compute monthly net results per category (stocks swing,
  stocks day trade, FIIs, ETFs), apply the stock-sale exemption, carry losses per
  the rules for each category, deduct IRRF, and apply the minimum-DARF carryover.
- **FR-009**: System MUST output DARF data per month: revenue code, period, due
  date, principal amount.
- **FR-010**: System MUST produce the annual return data: assets at 31/12,
  monthly variable-income table, exempt income, exclusive-taxation income.
- **FR-011**: The CLI MUST offer human-readable and JSON output, and CSV for the
  annual report.
- **FR-012**: Every rate, limit, code and date rule MUST come from
  `docs/regras-fiscais.md` with its legal source; unconfirmed rules raise or flag
  `UNVERIFIED` (Constitution I).
- **FR-013**: System MUST NOT make any network request and MUST NOT persist user
  data outside the output paths the user chooses (Constitution IV).
- **FR-014**: README and CLI MUST show the not-tax-advice disclaimer (Constitution VI).

### Key Entities

- **Operation**: a buy or sale — trade date, ticker, asset class, side,
  quantity, unit price, allocated costs, IRRF, source document, trade type
  (day/swing).
- **CorporateEvent**: split, reverse split, bonus share — ticker, date, ratio,
  cost attributed (for bonus shares).
- **IncomeEntry**: dividend, JCP, FII income — ticker, payment date, gross amount,
  withholding.
- **Position**: ticker, quantity, total cost, average price; derived from operations
  and events in date order.
- **MonthlyAssessment**: month, per-category net result, exemption applied, loss
  balances, IRRF used, tax due, carryover, DARF.
- **AnnualReport**: year, assets at 31/12, monthly table, exempt income,
  exclusive-taxation income.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For the synthetic fixture year, every monthly tax due, loss balance
  and DARF amount matches the hand-computed expected values to the cent.
- **SC-002**: Every rate, limit and DARF code in the code base is traceable to an
  entry with a legal source in `docs/regras-fiscais.md` (checked by a test).
- **SC-003**: A user can install with `pip install b3-ir` and get the monthly report
  for a folder of notes with a single command, in under 5 minutes from install.
- **SC-004**: Unsupported inputs (instrument, broker layout, event) never produce a
  silent number: 100% of them produce an explicit message in the fixture tests.
- **SC-005**: Processing one year of notes (up to 300 notes) completes in under
  30 seconds on a typical laptop.
- **SC-006**: No test or fixture contains real personal data (CPF, account, name).

## Assumptions

- Individual taxpayer resident in Brazil; only spot market (stocks, FIIs, ETFs).
  Options, futures, BDRs, fixed income, crypto and foreign assets are out of scope.
- Exact rates, exemption limit, minimum DARF, DARF codes, IRRF rates, due dates,
  cost-allocation and bonus-share cost rules are NOT fixed by this spec: they are
  confirmed with legal sources in `research.md` and `docs/regras-fiscais.md`,
  including any change from 2025–2026 legislation.
- SINACOR is the target note layout; broker-specific variants are added only when
  a fixture exists.
- The domain core is a Python port of the logic from the owner's private MonnaIA
  project (TypeScript), validated against the same hand-computed cases; MonnaIA
  code is not copied verbatim.
- Distribution as the `b3-ir` package on PyPI; publication only with the owner's
  authorization.
