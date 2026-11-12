from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from b3_ir.domain.classify import asset_class_of, classify
from b3_ir.domain.models import AssetClass, Side, TradeType
from b3_ir.errors import UnsupportedOperationError
from tests.unit.factories import op

D = date(2026, 3, 2)


@pytest.mark.parametrize(
    ("ticker", "expected"),
    [
        ("PETR4", AssetClass.STOCK),
        ("VALE3", AssetClass.STOCK),
        ("TAEE11", AssetClass.STOCK),
        ("BOVA11", AssetClass.ETF),
        ("HGLG11", AssetClass.FII),
    ],
)
def test_asset_class(ticker: str, expected: AssetClass) -> None:
    assert asset_class_of(ticker)[0] is expected


def test_fii_heuristic_warns_and_override_wins() -> None:
    assert asset_class_of("HGLG11")[1] is not None
    assert asset_class_of("XPTO11", {"XPTO11": AssetClass.ETF}) == (AssetClass.ETF, None)


@pytest.mark.parametrize("ticker", ["PETR4F", "BOVA11B", "AAPL34", "PETRA300"])
def test_out_of_scope_tickers_are_refused(ticker: str) -> None:
    with pytest.raises(UnsupportedOperationError):
        asset_class_of(ticker)


def test_same_day_buy_and_sell_is_day_trade() -> None:
    # Buy 300, sell 100 on the same day: 100 day trade + 200 swing buy.
    ops, _ = classify(
        [
            op(D, "PETR4", Side.BUY, "300", "10", costs="3.00"),
            op(D, "PETR4", Side.SELL, "100", "11", costs="1.00"),
        ]
    )
    summary = [(o.side, o.trade_type, o.quantity, o.costs) for o in ops]
    assert summary == [
        (Side.BUY, TradeType.DAY, Decimal("100"), Decimal("1.00")),
        (Side.BUY, TradeType.SWING, Decimal("200"), Decimal("2.00")),
        (Side.SELL, TradeType.DAY, Decimal("100"), Decimal("1.00")),
    ]


def test_day_trade_requires_the_same_broker() -> None:
    # Lei 9.959/2000, art. 8, par. 1, I, a: same day, same asset, same intermediary.
    buy = replace(op(D, "PETR4", Side.BUY, "100", "10"), broker="Corretora A")
    sell = replace(op(D, "PETR4", Side.SELL, "100", "11"), broker="Corretora B")
    ops, _ = classify([buy, sell])
    assert {o.trade_type for o in ops} == {TradeType.SWING}


def test_different_days_are_swing() -> None:
    ops, _ = classify(
        [
            op(D, "PETR4", Side.BUY, "100", "10"),
            op(date(2026, 3, 3), "PETR4", Side.SELL, "100", "11"),
        ]
    )
    assert {o.trade_type for o in ops} == {TradeType.SWING}
