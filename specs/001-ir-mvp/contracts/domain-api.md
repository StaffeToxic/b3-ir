# Domain API contract — `b3_ir`

All models are `@dataclass(frozen=True, slots=True)`; money and quantities are
`Decimal`; dates are `datetime.date`.

## Enums

```python
class AssetClass(StrEnum): STOCK = "acao"; FII = "fii"; ETF = "etf"
class Side(StrEnum): BUY = "compra"; SELL = "venda"
class TradeType(StrEnum): SWING = "comum"; DAY = "day_trade"
class EventKind(StrEnum): SPLIT = "desdobramento"; REVERSE_SPLIT = "grupamento"; BONUS = "bonificacao"
class IncomeKind(StrEnum): DIVIDEND = "dividendo"; JCP = "jcp"; FII_INCOME = "rendimento_fii"
class Category(StrEnum): STOCK_SWING = "acoes_comum"; STOCK_DAY = "acoes_day_trade"; FII = "fii"; ETF_SWING = "etf_comum"; ETF_DAY = "etf_day_trade"
```

## Models

```python
Operation(trade_date, settlement_date, ticker, side, quantity, unit_price,
          costs, irrf, source, asset_class: AssetClass | None = None,
          trade_type: TradeType | None = None)
# Parsers leave asset_class and trade_type as None; classify() fills both.
# Domain functions after classify() raise if either is still None.
CorporateEvent(date, ticker, kind, ratio: Decimal, bonus_unit_cost: Decimal | None, source)
IncomeEntry(payment_date, ticker, kind, gross, withheld, source)
Position(ticker, asset_class, quantity, total_cost)        # .average_price property
Darf(code: str, period: str, due_date, amount)              # period "AAAA-MM"
MonthlyAssessment(month, results: dict[Category, Decimal], exempt: Decimal,
                  loss_balances: dict[str, Decimal], irrf_used, tax_due,
                  carryover, darf: Darf | None, incomplete: bool, warnings: tuple[str, ...])
AnnualReport(year, assets, monthly_table, exempt_income, exclusive_income, warnings)
```

`source` is a short string: `"<file name>#<page or row>"` (never contains personal data).

## Rules registry (`b3_ir.rules`)

```python
Rule(id: str, value: Decimal | str | int, source: str, valid_from: date,
     valid_to: date | None, verified: bool)
def get(rule_id: str, on: date) -> Rule   # raises UnsupportedOperationError if none valid,
                                          # and flags UNVERIFIED if rule.verified is False
```

## Functions

```python
parse_sinacor(path) -> NoteParseResult(operations, warnings)
parse_b3_statement(path) -> StatementParseResult(operations, events, income, warnings)
deduplicate(ops) -> tuple[list[Operation], list[str]]
classify(ops) -> list[Operation]                 # fills asset_class and trade_type
build_positions(ops, events, until: date | None = None) -> PositionLedger
assess_months(ops, ledger, year) -> list[MonthlyAssessment]
build_annual_report(ops, events, income, year) -> AnnualReport
```

Errors: `ParseError(file, detail)`, `UnsupportedOperationError(item, reason)`;
both subclass `B3IRError`.
