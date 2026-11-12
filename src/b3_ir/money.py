"""Exact money helpers. Floats are rejected on purpose (Constitution II)."""

from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

ZERO = Decimal("0")
CENT = Decimal("0.01")

ROUNDING_MODES = {
    "half_up": ROUND_HALF_UP,
    "down": ROUND_DOWN,
}


def to_decimal(value: Decimal | int | str) -> Decimal:
    """Convert an exact input to Decimal.

    Accepts ``Decimal``, ``int`` and ``str`` (dot as decimal separator). ``float`` and
    ``bool`` are refused because they cannot represent money exactly.
    """
    if isinstance(value, bool | float):
        raise TypeError(f"valor monetário deve ser exato, recebido {type(value).__name__}")
    result = value if isinstance(value, Decimal) else Decimal(value)
    if not result.is_finite():
        raise ValueError(f"valor monetário inválido: {value!r}")
    return result


def parse_brl(text: str) -> Decimal:
    """Parse a Brazilian-formatted number such as ``"1.234,56"`` or ``"-0,01"``."""
    cleaned = text.strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    if not cleaned:
        raise ValueError("número vazio")
    return to_decimal(cleaned)


def quantize_cents(value: Decimal, rounding: str) -> Decimal:
    """Round to cents with an explicit mode; callers pass the mode cited in rules.py."""
    try:
        mode = ROUNDING_MODES[rounding]
    except KeyError:
        raise ValueError(f"modo de arredondamento desconhecido: {rounding}") from None
    return value.quantize(CENT, rounding=mode)
