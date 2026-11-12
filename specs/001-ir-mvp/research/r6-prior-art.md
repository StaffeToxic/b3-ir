# R6 — Prior art and MonnaIA inventory

Date: 2026-11-11. Source: private repo `StaffeToxic/MonnaIA` (TypeScript), read-only
shallow clone. External open-source prior art: see `research.md` D-R6-3.

## What MonnaIA has that is worth porting

| MonnaIA file | What it does | Port to b3-ir |
|---|---|---|
| `src/engine/positions.ts` | Weighted average cost engine over ledger events | Logic → `domain/positions.py`, with `Decimal` instead of `number` |
| `src/engine/movementCatalog.ts` | Maps B3 "Movimentação" labels to effects (quantity, income, cash, rights, checkpoint, review) | Label table → `parsers/b3_statements.py` (MVP subset) |
| `src/ingestion/excel/movimentacaoParser.ts` | Header-row detection, accent-insensitive column aliases, Entrada/Saída direction | Approach → `parsers/b3_statements.py` |
| `src/ingestion/excel/normalize.ts` | `extractTicker` from "PETR4 - PETROBRAS PN" product strings | Port with tests |
| `src/engine/utils.ts` | FII vs ETF heuristic for `*11` tickers with a hard-coded ETF list | Do NOT port as is; R4 decides a better offline source |
| `src/market/pipeline/b3StockUniverse.ts` | Uses COTAHIST market type `010` / BDI `02` to find stocks | Hint for R4: COTAHIST BDI codes can classify FII/ETF offline (UNVERIFIED) |

## Findings that change the b3-ir contract

1. **B3 reports splits as a quantity delta, not a ratio.** "Desdobro" credits N
   shares and "Grupamento" debits N shares in the Movimentação statement. MonnaIA
   adds the signed quantity and keeps total cost. → `CorporateEvent` carries
   `quantity_delta` (signed) instead of `ratio`. Decided in `research.md` D-R6-1.
2. **Same-day ordering:** credits (buys, bonus, splits) are applied before debits
   (sells) on the same date, otherwise a sale can hit an empty position. b3-ir
   keeps this order, but only for events; operations inside the same note keep
   the note order for day-trade matching.
3. **MonnaIA clamps oversold positions to zero**; b3-ir refuses instead
   (`UnsupportedOperationError`, Constitution VI).
4. Labels seen in real exports (from the catalog): `Transferência - Liquidação`
   (buy/sell by direction), `Rendimento`, `Dividendo`, `Juros Sobre Capital
   Próprio`, `Bonificação em Ativos`, `Desdobro`, `Agrupamento`, `Leilão de Fração`,
   `Fração em Ativos`, `Atualização`, `Direitos de Subscrição*`, `Empréstimo`,
   `Transferência`. Suffix ` - Transferido` must be stripped.
   MVP maps the first seven; the rest are reported as unsupported or ignored with
   a warning.

## What MonnaIA does NOT have

- No SINACOR PDF parser (it ingests B3 XLSX exports and a crypto statement).
- No tax logic: no exemption, loss carryover, IRRF, DARF or DIRPF mapping.
- Uses `number` (float) for money, so its numbers cannot be reused as golden values.

## Test cases worth porting

`test/engine/positions.test.ts` (378 lines) and `test/ingestion/parsers.test.ts`
(200 lines): scenarios for buy/sell/bonus/split sequences and statement parsing.
Re-derive expected values by hand in `Decimal` (Constitution III); do not copy
float expectations.
