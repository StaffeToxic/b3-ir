"""Annual report with hand-computed values."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from b3_ir.domain.annual import (
    EXCLUSIVE_JCP,
    EXEMPT_DIVIDENDS,
    EXEMPT_FII_INCOME,
    EXEMPT_STOCK_GAINS,
    build_annual_report,
)
from b3_ir.domain.classify import classify
from b3_ir.domain.models import AnnualReport, IncomeEntry, IncomeKind, Operation, Side
from b3_ir.report.csv_out import write_annual_csv
from tests.unit.factories import op


def report(ops: Sequence[Operation], year: int, income: Sequence[IncomeEntry] = ()) -> AnnualReport:
    classified, _ = classify(ops)
    return build_annual_report(classified, [], income, year)


def income(day: date, ticker: str, kind: IncomeKind, gross: str) -> IncomeEntry:
    return IncomeEntry(day, ticker, kind, Decimal(gross), Decimal(0), "x")


def test_assets_show_previous_and_current_year() -> None:
    # 2025: 100 @ 10 = 1,000. 2026: +100 @ 12 = 1,200 -> 200 shares, 2,200.
    # WEGE3 bought in 2025 (300) and sold out in 2026: listed with zero to close it.
    result = report(
        [
            op(date(2025, 3, 3), "ITSA4", Side.BUY, "100", "10"),
            op(date(2025, 4, 1), "WEGE3", Side.BUY, "10", "30"),
            op(date(2026, 2, 2), "ITSA4", Side.BUY, "100", "12"),
            op(date(2026, 5, 5), "WEGE3", Side.SELL, "10", "35"),
        ],
        2026,
    )
    assets = {a.ticker: a for a in result.assets}
    itsa = assets["ITSA4"]
    assert (itsa.quantity, itsa.cost_previous_year, itsa.cost) == (
        Decimal("200"),
        Decimal("1000"),
        Decimal("2200"),
    )
    assert itsa.average_price == Decimal("11")
    wege = assets["WEGE3"]
    assert (wege.quantity, wege.cost_previous_year, wege.cost) == (0, Decimal("300"), 0)
    # WEGE3 gain 50 with sales 350 <= 20,000: exempt.
    assert result.exempt_income[EXEMPT_STOCK_GAINS] == Decimal("50")


def test_losses_from_previous_year_carry_into_the_report() -> None:
    # 2025: loss 1,000 (sales 30,000 -> not exempt). 2026: gain 1,500 with sales 31,500
    # -> 1,500 - 1,000 = 500 taxable -> 75.00 DARF.
    result = report(
        [
            op(date(2025, 1, 6), "PETR4", Side.BUY, "1000", "31"),
            op(date(2025, 2, 3), "PETR4", Side.SELL, "1000", "30"),
            op(date(2026, 1, 6), "VALE3", Side.BUY, "500", "60"),
            op(date(2026, 2, 3), "VALE3", Side.SELL, "500", "63"),
        ],
        2026,
    )
    (feb,) = result.monthly_table
    assert feb.darf is not None
    assert feb.darf.amount == Decimal("75.00")


def test_income_totals_and_warnings_2026() -> None:
    result = report(
        [],
        2026,
        [
            income(date(2026, 3, 10), "ITSA4", IncomeKind.DIVIDEND, "60000"),
            income(date(2026, 4, 10), "ITSA4", IncomeKind.DIVIDEND, "100"),
            income(date(2026, 3, 15), "HGLG11", IncomeKind.FII_INCOME, "110"),
            income(date(2026, 6, 1), "ITSA4", IncomeKind.JCP, "85"),
            income(date(2025, 12, 30), "ITSA4", IncomeKind.DIVIDEND, "999"),  # other year
        ],
    )
    assert result.exempt_income[EXEMPT_DIVIDENDS] == Decimal("60100")
    assert result.exempt_income[EXEMPT_FII_INCOME] == Decimal("110")
    assert result.exclusive_income[EXCLUSIVE_JCP] == Decimal("85")
    text = " | ".join(result.warnings)
    assert "100 cotistas" in text
    assert "17,5% em 2026" in text  # LC 224/2025
    assert "dividendos de ITSA4 em 2026-03 somam R$ 60000,00" in text
    assert "2026-04" not in text


def test_2025_uses_previous_jcp_rate_and_no_dividend_withholding() -> None:
    result = report(
        [],
        2025,
        [
            income(date(2025, 6, 1), "ITSA4", IncomeKind.JCP, "85"),
            income(date(2025, 3, 10), "ITSA4", IncomeKind.DIVIDEND, "60000"),
        ],
    )
    text = " | ".join(result.warnings)
    assert "15% em 2025" in text
    assert "acima de" not in text


def test_csv_files(tmp_path: Path) -> None:
    result = report([op(date(2026, 3, 3), "ITSA4", Side.BUY, "100", "10.5")], 2026)
    paths = write_annual_csv(result, tmp_path)
    assert [p.name for p in paths] == [
        "bens_e_direitos.csv",
        "renda_variavel.csv",
        "rendimentos_isentos.csv",
        "tributacao_exclusiva.csv",
    ]
    raw = paths[0].read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM for Excel
    lines = raw.decode("utf-8-sig").splitlines()
    assert lines == [
        "ticker;classe;quantidade;situacao_2025;situacao_2026",
        "ITSA4;acao;100;0,00;1050,00",
    ]
