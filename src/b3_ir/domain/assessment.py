"""Monthly assessment: exemption, loss offsetting, IRRF, minimum DARF (FR-008, FR-009).

Every constant comes from b3_ir.rules; while a rule is unverified the month carries
an ``UNVERIFIED`` warning (Constitution I).
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal

from b3_ir import rules
from b3_ir.domain.models import AssetClass, Category, Darf, MonthlyAssessment, TradeType
from b3_ir.domain.positions import RealizedResult
from b3_ir.money import ZERO, quantize_cents

BUCKET_COMMON = "comum"
BUCKET_DAY = "day_trade"
BUCKET_FII = "fii"

_RATE_RULE = {
    BUCKET_COMMON: "stock_swing_rate",
    BUCKET_DAY: "day_trade_rate",
    BUCKET_FII: "fii_rate",
}


@dataclass(frozen=True, slots=True)
class CarryState:
    """Balances carried from one month to the next (and across years)."""

    losses: tuple[tuple[str, Decimal], ...] = (
        (BUCKET_COMMON, ZERO),
        (BUCKET_DAY, ZERO),
        (BUCKET_FII, ZERO),
    )
    irrf: Decimal = ZERO
    tax_below_minimum: Decimal = ZERO

    def loss(self, bucket: str) -> Decimal:
        return dict(self.losses)[bucket]


def category_of(result: RealizedResult) -> Category:
    if result.asset_class is AssetClass.FII:
        return Category.FII
    day = result.trade_type is TradeType.DAY
    if result.asset_class is AssetClass.ETF:
        return Category.ETF_DAY if day else Category.ETF_SWING
    return Category.STOCK_DAY if day else Category.STOCK_SWING


def last_business_day(year: int, month: int) -> date:
    """Last weekday of the month. National holidays are not considered yet."""
    day = date(year, month, calendar.monthrange(year, month)[1])
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def _due_date(year: int, month: int) -> date:
    return last_business_day(year + month // 12, month % 12 + 1)


class _Rules:
    """Rules resolved for one month, remembering which ones are unverified."""

    def __init__(self, on: date) -> None:
        self.on = on
        self.unverified: list[str] = []

    def number(self, rule_id: str) -> Decimal:
        value, unverified = rules.decimal_rule(rule_id, self.on)
        self.track(rule_id, unverified)
        return value

    def text(self, rule_id: str) -> str:
        resolved = rules.get(rule_id, self.on)
        self.track(rule_id, resolved.unverified)
        return str(resolved.value)

    def track(self, rule_id: str, unverified: bool) -> None:
        if unverified and rule_id not in self.unverified:
            self.unverified.append(rule_id)


def _offset(value: Decimal, loss: Decimal) -> tuple[Decimal, Decimal]:
    """Return (taxable, new loss balance) after offsetting carried losses."""
    if value < ZERO:
        return ZERO, loss - value
    used = min(loss, value)
    return value - used, loss - used


def assess_month(
    year: int, month: int, results: Iterable[RealizedResult], carry: CarryState
) -> tuple[MonthlyAssessment, CarryState]:
    month_start = date(year, month, 1)
    r = _Rules(month_start)
    per_category: dict[Category, Decimal] = defaultdict(lambda: ZERO)
    stock_swing_sales = ZERO
    irrf = ZERO
    for item in results:
        category = category_of(item)
        per_category[category] += item.result
        irrf += item.irrf
        if category is Category.STOCK_SWING:
            stock_swing_sales += item.sale_value

    stock_swing = per_category[Category.STOCK_SWING]
    exempt = ZERO
    if stock_swing > ZERO and stock_swing_sales <= r.number("stock_sale_exemption_limit"):
        exempt, stock_swing = stock_swing, ZERO

    bucket_values = {
        BUCKET_COMMON: stock_swing + per_category[Category.ETF_SWING],
        BUCKET_DAY: per_category[Category.STOCK_DAY] + per_category[Category.ETF_DAY],
        BUCKET_FII: per_category[Category.FII],
    }
    tax = ZERO
    losses: dict[str, Decimal] = {}
    for bucket, value in bucket_values.items():
        taxable, losses[bucket] = _offset(value, carry.loss(bucket))
        if taxable > ZERO:
            tax += taxable * r.number(_RATE_RULE[bucket])

    irrf_available = irrf + carry.irrf
    irrf_used = min(tax, irrf_available)
    tax_due = tax - irrf_used
    exact = tax_due + carry.tax_below_minimum
    rounding = rules.get("money_rounding", month_start)
    payable = quantize_cents(exact, str(rounding.value))
    if payable != exact:
        r.track("money_rounding", rounding.unverified)

    warnings = [
        "vencimento do DARF não considera feriados nacionais",
    ]
    darf: Darf | None = None
    carryover = ZERO
    if payable == ZERO:
        pass
    elif payable < r.number("minimum_darf"):
        carryover = payable
        warnings.append(f"imposto de R$ {payable} abaixo do mínimo; acumulado para o mês seguinte")
    else:
        r.text("darf_due_rule")
        darf = Darf(
            code=r.text("darf_code_variable_income"),
            period=f"{year:04d}-{month:02d}",
            due_date=_due_date(year, month),
            amount=payable,
        )
    if r.unverified:
        warnings.insert(0, f"{rules.UNVERIFIED}: regras não confirmadas: {', '.join(r.unverified)}")

    assessment = MonthlyAssessment(
        month=f"{year:04d}-{month:02d}",
        results={category: per_category[category] for category in Category},
        exempt=exempt,
        loss_balances=dict(losses),
        irrf_used=irrf_used,
        tax_due=tax_due,
        carryover=carryover,
        darf=darf,
        incomplete=False,
        warnings=tuple(warnings),
    )
    next_carry = replace(
        carry,
        losses=tuple(losses.items()),
        irrf=irrf_available - irrf_used,
        tax_below_minimum=carryover,
    )
    return assessment, next_carry


def assess_year(
    realized: Iterable[RealizedResult], year: int, opening: CarryState | None = None
) -> tuple[list[MonthlyAssessment], CarryState]:
    """Assess every month of ``year`` that has realized results, chaining the carry state."""
    by_month: dict[int, list[RealizedResult]] = defaultdict(list)
    for item in realized:
        if item.date.year == year:
            by_month[item.date.month].append(item)
    carry = opening or CarryState()
    assessments: list[MonthlyAssessment] = []
    for month in range(1, 13):
        if month not in by_month and carry.tax_below_minimum == ZERO:
            continue
        assessment, carry = assess_month(year, month, by_month.get(month, []), carry)
        assessments.append(assessment)
    if carry.irrf > ZERO:
        # Withheld tax does not carry into next year's monthly assessment: the 0.005%
        # balance goes to the annual return (Lei 11.033/2004, art. 2º, § 7º, III) and the
        # day-trade balance to a refund request (IN RFB 1.585/2015, art. 65, § 9º).
        note = (
            f"saldo de IRRF de R$ {quantize_cents(carry.irrf, 'half_up')} não compensado "
            f"em {year}: declaração de ajuste (0,005%) ou pedido de restituição (day trade)"
        )
        if assessments:
            last = assessments[-1]
            assessments[-1] = replace(last, warnings=(*last.warnings, note))
        carry = replace(carry, irrf=ZERO)
    return assessments, carry
