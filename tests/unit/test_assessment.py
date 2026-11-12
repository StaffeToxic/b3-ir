"""Monthly assessment with hand-computed values.

Rates and limits used below are the current candidates in rules.py (15% common,
20% day trade and FII, R$ 20,000 exemption, R$ 10 minimum DARF), still UNVERIFIED.
"""

from datetime import date
from decimal import Decimal

import pytest

from b3_ir.domain.assessment import (
    BUCKET_COMMON,
    BUCKET_DAY,
    BUCKET_FII,
    CarryState,
    assess_year,
    last_business_day,
)
from b3_ir.domain.models import AssetClass, Category, TradeType
from b3_ir.domain.positions import RealizedResult


def res(
    day: date,
    result: str,
    sale_value: str,
    asset_class: AssetClass = AssetClass.STOCK,
    trade_type: TradeType = TradeType.SWING,
    irrf: str = "0",
) -> RealizedResult:
    return RealizedResult(
        day, "XXXX3", asset_class, trade_type, Decimal(sale_value), Decimal(result), Decimal(irrf)
    )


def by_month(results: list[RealizedResult]):  # type: ignore[no-untyped-def]
    assessments, carry = assess_year(results, 2026)
    return {a.month: a for a in assessments}, carry


def test_stock_gain_under_limit_is_exempt() -> None:
    # Sales 6,000 <= 20,000 and gain 1,000: exempt, no tax, no DARF.
    months, _ = by_month([res(date(2026, 2, 10), "1000", "6000")])
    feb = months["2026-02"]
    assert (feb.exempt, feb.tax_due, feb.darf) == (Decimal("1000"), 0, None)


def test_loss_is_carried_and_offset_then_irrf_deducted() -> None:
    # Feb: loss 1,000 (sales 5,000). Mar: gain 5,000, sales 30,000 > limit.
    # Taxable 5,000 - 1,000 = 4,000; 15% = 600.00; IRRF 1.50 -> DARF 598.50,
    # due on the last business day of April 2026 (Thursday 30).
    months, carry = by_month(
        [
            res(date(2026, 2, 10), "-1000", "5000"),
            res(date(2026, 3, 10), "5000", "30000", irrf="1.50"),
        ]
    )
    assert months["2026-02"].loss_balances[BUCKET_COMMON] == Decimal("1000")
    mar = months["2026-03"]
    assert mar.loss_balances[BUCKET_COMMON] == 0
    assert mar.irrf_used == Decimal("1.50")
    assert mar.darf is not None
    assert (mar.darf.code, mar.darf.amount, mar.darf.due_date) == (
        "6015",
        Decimal("598.50"),
        date(2026, 4, 30),
    )
    assert carry.loss(BUCKET_COMMON) == 0


def test_day_trade_taxed_at_its_own_rate() -> None:
    # Day trade gain 100 -> 20% = 20.00, IRRF 1.00 -> DARF 19.00 due Fri 2026-05-29.
    months, _ = by_month(
        [res(date(2026, 4, 15), "100", "1000", trade_type=TradeType.DAY, irrf="1.00")]
    )
    apr = months["2026-04"]
    assert apr.results[Category.STOCK_DAY] == Decimal("100")
    assert apr.darf is not None
    assert (apr.darf.amount, apr.darf.due_date) == (Decimal("19.00"), date(2026, 5, 29))


def test_day_trade_gain_is_never_exempt() -> None:
    months, _ = by_month([res(date(2026, 4, 15), "100", "500", trade_type=TradeType.DAY)])
    assert months["2026-04"].exempt == 0


def test_tax_below_minimum_accumulates() -> None:
    # Jun: ETF gain 40 -> 6.00 < 10: carried. Jul: 6.00 + 6.00 = 12.00 -> DARF, due Mon 2026-08-31.
    months, carry = by_month(
        [
            res(date(2026, 6, 10), "40", "1000", asset_class=AssetClass.ETF),
            res(date(2026, 7, 10), "40", "1000", asset_class=AssetClass.ETF),
        ]
    )
    assert months["2026-06"].darf is None
    assert months["2026-06"].carryover == Decimal("6.00")
    jul = months["2026-07"]
    assert jul.darf is not None
    assert (jul.darf.amount, jul.darf.due_date) == (Decimal("12.00"), date(2026, 8, 31))
    assert carry.tax_below_minimum == 0


def test_etf_gain_is_not_exempt() -> None:
    months, _ = by_month([res(date(2026, 6, 10), "100", "1000", asset_class=AssetClass.ETF)])
    assert months["2026-06"].exempt == 0
    assert months["2026-06"].darf is not None


def test_fii_loss_does_not_offset_stock_gain() -> None:
    # FII -500 stays in the FII bucket; stock gain 1,000 with sales 25,000 -> 150.00.
    months, carry = by_month(
        [
            res(date(2026, 8, 5), "-500", "3000", asset_class=AssetClass.FII),
            res(date(2026, 8, 6), "1000", "25000"),
        ]
    )
    aug = months["2026-08"]
    assert aug.darf is not None
    assert aug.darf.amount == Decimal("150.00")
    assert carry.loss(BUCKET_FII) == Decimal("500")


def test_loss_in_exempt_month_still_counts() -> None:
    # Sales under the limit but a loss: the loss is carried (rule to confirm in R1).
    _, carry = by_month([res(date(2026, 2, 10), "-300", "2000")])
    assert carry.loss(BUCKET_COMMON) == Decimal("300")


def test_irrf_surplus_is_carried() -> None:
    _, carry = by_month([res(date(2026, 2, 10), "-10", "30000", irrf="1.50")])
    assert carry.irrf == Decimal("1.50")


def test_opening_state_from_previous_year() -> None:
    opening = CarryState(
        losses=(
            (BUCKET_COMMON, Decimal("0")),
            (BUCKET_DAY, Decimal("50")),
            (BUCKET_FII, Decimal("0")),
        )
    )
    assessments, _ = assess_year(
        [res(date(2026, 1, 20), "50", "1000", trade_type=TradeType.DAY)], 2026, opening
    )
    assert assessments[0].tax_due == 0


def test_every_month_is_flagged_unverified_while_rules_are_candidates() -> None:
    months, _ = by_month([res(date(2026, 3, 10), "5000", "30000")])
    assert months["2026-03"].warnings[0].startswith("UNVERIFIED")


@pytest.mark.parametrize(
    ("year", "month", "expected"),
    [(2026, 5, date(2026, 5, 29)), (2026, 8, date(2026, 8, 31)), (2026, 12, date(2026, 12, 31))],
)
def test_last_business_day(year: int, month: int, expected: date) -> None:
    assert last_business_day(year, month) == expected


def test_december_darf_is_due_in_january() -> None:
    months, _ = by_month([res(date(2026, 12, 10), "1000", "30000")])
    dec = months["2026-12"]
    assert dec.darf is not None
    assert dec.darf.due_date == date(2027, 1, 29)
