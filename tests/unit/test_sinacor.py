"""SINACOR adapter, tested with fakes shaped like correpy's entities (no AGPL dependency)."""

import builtins
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import pytest

from b3_ir.domain.models import Side
from b3_ir.errors import ParseError
from b3_ir.parsers.sinacor import INSTALL_HINT, notes_to_operations, parse_sinacor


class FakeType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class FakeSecurity:
    name: str
    ticker: str | None


@dataclass
class FakeTransaction:
    transaction_type: FakeType
    amount: Decimal
    unit_price: Decimal
    security: FakeSecurity


@dataclass
class FakeNote:
    reference_id: int
    reference_date: date
    settlement_fee: Decimal = Decimal(0)
    emoluments: Decimal = Decimal(0)
    irrf: Decimal = Decimal(0)
    transactions: list[FakeTransaction] = field(default_factory=list)


def trade(kind: FakeType, ticker: str | None, qty: str, price: str) -> FakeTransaction:
    return FakeTransaction(kind, Decimal(qty), Decimal(price), FakeSecurity(f"{ticker} ON", ticker))


def test_fees_and_irrf_follow_the_note() -> None:
    # Gross: buy 3,000 + sell 1,000 = 4,000; fees 2.00 + 0.40 = 2.40 -> 1.80 / 0.60.
    # Note IRRF 0.05 goes entirely to the only sale.
    note = FakeNote(
        123,
        date(2026, 3, 2),
        settlement_fee=Decimal("2.00"),
        emoluments=Decimal("0.40"),
        irrf=Decimal("0.05"),
        transactions=[
            trade(FakeType.BUY, "PETR4", "100", "30"),
            trade(FakeType.SELL, "VALE3", "10", "100"),
        ],
    )
    result = notes_to_operations([note], "nota.pdf", broker="XP")
    buy, sell = result.operations
    assert (buy.side, buy.costs, buy.irrf, buy.broker) == (Side.BUY, Decimal("1.8"), 0, "XP")
    assert (sell.side, sell.costs, sell.irrf) == (Side.SELL, Decimal("0.60"), Decimal("0.05"))
    assert sell.source == "nota.pdf#nota123"
    assert result.unsupported == []


def test_irrf_split_between_sales_by_value() -> None:
    note = FakeNote(
        1,
        date(2026, 3, 2),
        irrf=Decimal("0.04"),
        transactions=[
            trade(FakeType.SELL, "PETR4", "100", "30"),  # 3,000 -> 0.03
            trade(FakeType.SELL, "VALE3", "10", "100"),  # 1,000 -> 0.01
        ],
    )
    ops = notes_to_operations([note], "n.pdf").operations
    assert [op.irrf for op in ops] == [Decimal("0.03"), Decimal("0.01")]


def test_note_with_out_of_scope_item_is_refused_whole() -> None:
    note = FakeNote(
        7,
        date(2026, 3, 2),
        settlement_fee=Decimal("1"),
        transactions=[
            trade(FakeType.BUY, "PETR4", "100", "30"),
            trade(FakeType.BUY, "AAPL34", "10", "50"),  # BDR: out of MVP scope
        ],
    )
    result = notes_to_operations([note], "n.pdf")
    assert result.operations == []
    assert any("AAPL34" in item for item in result.unsupported)
    assert any("ignorada inteira" in item for item in result.unsupported)


def test_missing_ticker_is_reported_not_guessed() -> None:
    note = FakeNote(8, date(2026, 3, 2), transactions=[trade(FakeType.BUY, None, "1", "1")])
    result = notes_to_operations([note], "n.pdf")
    assert result.operations == []
    assert "ticker não identificado" in result.unsupported[0]


def test_irrf_without_sales_is_an_error() -> None:
    note = FakeNote(
        9,
        date(2026, 3, 2),
        irrf=Decimal("0.01"),
        transactions=[trade(FakeType.BUY, "PETR4", "1", "1")],
    )
    with pytest.raises(ParseError, match="sem vendas"):
        notes_to_operations([note], "n.pdf")


def test_missing_extra_gives_install_hint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith("correpy"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    pdf = tmp_path / "nota.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    with pytest.raises(ParseError) as exc:
        parse_sinacor(pdf)
    assert INSTALL_HINT in str(exc.value)


def test_unreadable_pdf_is_a_parse_error(tmp_path: Path) -> None:
    pytest.importorskip("correpy")
    pdf = tmp_path / "quebrado.pdf"
    pdf.write_bytes(b"isto nao e um pdf")
    with pytest.raises(ParseError, match="não reconhecida"):
        parse_sinacor(pdf)
