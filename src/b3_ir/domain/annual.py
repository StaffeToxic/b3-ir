"""Annual return data (FR-010, research D-R5-1).

Builds what the investor copies into the DIRPF: assets at 31/12 (current and
previous year, at acquisition cost), the monthly variable-income table, exempt
income and income taxed exclusively at source. Form codes (group/code of "Bens e
Direitos", income-type numbers) change with each year's program and were not found
in an official text, so the report names the fields instead of numbering them.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal

from b3_ir import rules
from b3_ir.domain.assessment import CarryState, assess_year
from b3_ir.domain.models import (
    AnnualReport,
    AssetEntry,
    CorporateEvent,
    IncomeEntry,
    IncomeKind,
    Operation,
)
from b3_ir.domain.positions import build_positions
from b3_ir.errors import UnsupportedOperationError
from b3_ir.money import ZERO, brl_text

EXEMPT_STOCK_GAINS = "ganhos_acoes_ate_20_mil"
EXEMPT_DIVIDENDS = "dividendos"
EXEMPT_FII_INCOME = "rendimentos_fii"
EXCLUSIVE_JCP = "jcp"


def _assets(
    operations: Sequence[Operation], events: Sequence[CorporateEvent], year: int
) -> tuple[AssetEntry, ...]:
    previous = build_positions(operations, events, until=date(year - 1, 12, 31)).positions
    current = build_positions(operations, events, until=date(year, 12, 31)).positions
    entries = []
    for ticker in sorted(set(previous) | set(current)):
        before, now = previous.get(ticker), current.get(ticker)
        held_before = before is not None and before.quantity > ZERO
        held_now = now is not None and now.quantity > ZERO
        if not (held_before or held_now):
            continue
        reference = now or before
        assert reference is not None
        entries.append(
            AssetEntry(
                ticker=ticker,
                asset_class=reference.asset_class,
                quantity=now.quantity if now else ZERO,
                cost_previous_year=before.total_cost if before else ZERO,
                cost=now.total_cost if now else ZERO,
            )
        )
    return tuple(entries)


def _percent(rate: Decimal) -> str:
    """0.175 -> "17,5%"."""
    return f"{(rate * 100).normalize():f}".replace(".", ",") + "%"


def _income_warnings(income: Sequence[IncomeEntry], year: int) -> list[str]:
    warnings: list[str] = []
    if any(i.kind is IncomeKind.FII_INCOME for i in income):
        warnings.append(
            "rendimentos de FII são isentos só se o fundo tiver ao menos 100 cotistas e você "
            "tiver menos de 10% das cotas (Lei 11.033/2004, art. 3º, III e § 1º); confira"
        )
    jcp = [i for i in income if i.kind is IncomeKind.JCP]
    if jcp:
        rate, _ = rules.decimal_rule("jcp_withholding_rate", jcp[0].payment_date)
        warnings.append(
            f"JCP é tributado exclusivamente na fonte ({_percent(rate)} em {year}); confira no "
            "informe de rendimentos se o valor do extrato é bruto ou líquido"
        )
    try:
        threshold, _ = rules.decimal_rule("dividend_monthly_threshold", date(year, 1, 1))
    except UnsupportedOperationError:
        return warnings  # no withholding on dividends before 2026
    per_month: dict[tuple[str, int], Decimal] = defaultdict(lambda: ZERO)
    for item in income:
        if item.kind is IncomeKind.DIVIDEND:
            per_month[(item.ticker, item.payment_date.month)] += item.gross
    for (ticker, month), total in sorted(per_month.items()):
        if total > threshold:
            warnings.append(
                f"dividendos de {ticker} em {year}-{month:02d} somam R$ "
                f"{brl_text(total)}, acima de R$ {brl_text(threshold)}: há retenção "
                "de 10% na fonte (Lei 9.250/1995, art. 6º-A); o limite é por empresa"
            )
    return warnings


def build_annual_report(
    operations: Sequence[Operation],
    events: Sequence[CorporateEvent],
    income: Iterable[IncomeEntry],
    year: int,
) -> AnnualReport:
    """Annual return data for ``year`` from classified operations, events and income."""
    ledger = build_positions(operations, events, until=date(year, 12, 31))
    opening: CarryState | None = None
    for previous in sorted({r.date.year for r in ledger.realized if r.date.year < year}):
        _, opening = assess_year(ledger.realized, previous, opening)
    months, _ = assess_year(ledger.realized, year, opening)

    in_year = [i for i in income if i.payment_date.year == year]

    def total(kind: IncomeKind) -> Decimal:
        return sum((i.gross for i in in_year if i.kind is kind), ZERO)

    # Month warnings stay on each month of monthly_table; these are the year's own.
    warnings = _income_warnings(in_year, year)
    warnings.append(
        "os códigos das fichas (grupo/código, tipo de rendimento) mudam a cada ano: "
        "use os nomes deste relatório para localizá-los no programa da Receita"
    )

    return AnnualReport(
        year=year,
        assets=_assets(operations, events, year),
        monthly_table=tuple(months),
        exempt_income={
            EXEMPT_STOCK_GAINS: sum((m.exempt for m in months), ZERO),
            EXEMPT_DIVIDENDS: total(IncomeKind.DIVIDEND),
            EXEMPT_FII_INCOME: total(IncomeKind.FII_INCOME),
        },
        exclusive_income={EXCLUSIVE_JCP: total(IncomeKind.JCP)},
        warnings=tuple(warnings),
    )
