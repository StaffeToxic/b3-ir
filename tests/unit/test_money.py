from decimal import Decimal

import pytest

from b3_ir.money import parse_brl, quantize_cents, to_decimal


def test_to_decimal_accepts_exact_types() -> None:
    assert to_decimal("10.50") == Decimal("10.50")
    assert to_decimal(3) == Decimal(3)
    assert to_decimal(Decimal("1.1")) == Decimal("1.1")


@pytest.mark.parametrize("value", [1.5, True])
def test_to_decimal_rejects_inexact_types(value: object) -> None:
    with pytest.raises(TypeError):
        to_decimal(value)  # type: ignore[arg-type]


def test_to_decimal_rejects_non_finite() -> None:
    with pytest.raises(ValueError, match="inválido"):
        to_decimal("NaN")


@pytest.mark.parametrize(
    ("text", "expected"),
    [("1.234,56", "1234.56"), ("-0,01", "-0.01"), ("R$ 10,00", "10.00"), ("7", "7")],
)
def test_parse_brl(text: str, expected: str) -> None:
    assert parse_brl(text) == Decimal(expected)


def test_parse_brl_empty() -> None:
    with pytest.raises(ValueError, match="vazio"):
        parse_brl("  ")


def test_quantize_cents_modes() -> None:
    assert quantize_cents(Decimal("1.005"), "half_up") == Decimal("1.01")
    assert quantize_cents(Decimal("1.009"), "down") == Decimal("1.00")
    with pytest.raises(ValueError, match="desconhecido"):
        quantize_cents(Decimal("1"), "banker")
