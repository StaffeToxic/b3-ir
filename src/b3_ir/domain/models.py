"""Domain models, per specs/001-ir-mvp/contracts/domain-api.md.

All models are immutable; money and quantities are Decimal; dates are datetime.date.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum

from b3_ir.money import ZERO


class AssetClass(StrEnum):
    STOCK = "acao"
    FII = "fii"
    ETF = "etf"


class Side(StrEnum):
    BUY = "compra"
    SELL = "venda"


class TradeType(StrEnum):
    SWING = "comum"
    DAY = "day_trade"


class EventKind(StrEnum):
    SPLIT = "desdobramento"
    REVERSE_SPLIT = "grupamento"
    BONUS = "bonificacao"


class IncomeKind(StrEnum):
    DIVIDEND = "dividendo"
    JCP = "jcp"
    FII_INCOME = "rendimento_fii"


class Category(StrEnum):
    STOCK_SWING = "acoes_comum"
    STOCK_DAY = "acoes_day_trade"
    FII = "fii"
    ETF_SWING = "etf_comum"
    ETF_DAY = "etf_day_trade"


def _require_decimal(name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} deve ser Decimal, recebido {type(value).__name__}")


def _require_non_negative(name: str, value: Decimal) -> None:
    _require_decimal(name, value)
    if value < ZERO:
        raise ValueError(f"{name} não pode ser negativo: {value}")


@dataclass(frozen=True, slots=True)
class Operation:
    """A buy or sale. Parsers leave asset_class/trade_type as None; classify() fills them."""

    trade_date: date
    settlement_date: date
    ticker: str
    side: Side
    quantity: Decimal
    unit_price: Decimal
    costs: Decimal
    irrf: Decimal
    source: str
    asset_class: AssetClass | None = None
    trade_type: TradeType | None = None

    def __post_init__(self) -> None:
        if not self.ticker or self.ticker != self.ticker.strip().upper():
            raise ValueError(f"ticker inválido: {self.ticker!r}")
        if self.quantity <= ZERO:
            raise ValueError(f"quantidade deve ser positiva: {self.quantity}")
        _require_non_negative("unit_price", self.unit_price)
        _require_non_negative("costs", self.costs)
        _require_non_negative("irrf", self.irrf)
        if self.settlement_date < self.trade_date:
            raise ValueError("liquidação anterior ao pregão")

    @property
    def gross_value(self) -> Decimal:
        return self.quantity * self.unit_price


@dataclass(frozen=True, slots=True)
class CorporateEvent:
    """Split, reverse split or bonus, as B3 reports it: shares credited or debited.

    ``quantity_delta`` is signed: positive for split and bonus credits, negative for
    reverse splits (research.md D-R6-1).
    """

    date: date
    ticker: str
    kind: EventKind
    quantity_delta: Decimal
    bonus_unit_cost: Decimal | None
    source: str

    def __post_init__(self) -> None:
        _require_decimal("quantity_delta", self.quantity_delta)
        if self.quantity_delta == ZERO:
            raise ValueError("evento sem variação de quantidade")
        expected_negative = self.kind is EventKind.REVERSE_SPLIT
        if (self.quantity_delta < ZERO) != expected_negative:
            raise ValueError(
                f"sinal de quantidade incompatível com {self.kind}: {self.quantity_delta}"
            )
        if self.kind is EventKind.BONUS:
            if self.bonus_unit_cost is None:
                raise ValueError("bonificação exige custo unitário atribuído")
            _require_non_negative("bonus_unit_cost", self.bonus_unit_cost)


@dataclass(frozen=True, slots=True)
class IncomeEntry:
    payment_date: date
    ticker: str
    kind: IncomeKind
    gross: Decimal
    withheld: Decimal
    source: str

    def __post_init__(self) -> None:
        _require_non_negative("gross", self.gross)
        _require_non_negative("withheld", self.withheld)


@dataclass(frozen=True, slots=True)
class Position:
    ticker: str
    asset_class: AssetClass
    quantity: Decimal
    total_cost: Decimal

    def __post_init__(self) -> None:
        _require_non_negative("quantity", self.quantity)
        _require_non_negative("total_cost", self.total_cost)

    @property
    def average_price(self) -> Decimal:
        if self.quantity == ZERO:
            return ZERO
        return self.total_cost / self.quantity


@dataclass(frozen=True, slots=True)
class Darf:
    code: str
    period: str
    due_date: date
    amount: Decimal


@dataclass(frozen=True, slots=True)
class MonthlyAssessment:
    month: str
    results: dict[Category, Decimal]
    exempt: Decimal
    loss_balances: dict[str, Decimal]
    irrf_used: Decimal
    tax_due: Decimal
    carryover: Decimal
    darf: Darf | None
    incomplete: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class AnnualReport:
    year: int
    assets: tuple[Position, ...]
    monthly_table: tuple[MonthlyAssessment, ...]
    exempt_income: dict[str, Decimal]
    exclusive_income: dict[str, Decimal]
    warnings: tuple[str, ...] = field(default_factory=tuple)
