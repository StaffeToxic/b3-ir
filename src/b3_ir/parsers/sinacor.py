"""SINACOR brokerage notes (PDF) via correpy (FR-001, research D-R4-1).

correpy depends on PyMuPDF (AGPL-3.0), so it is an optional extra
(``pip install "b3-ir[pdf]"``) imported only when a PDF is read; the rest of b3-ir
stays free of AGPL code.

What b3-ir takes from correpy is only what the note states: trades, fees and the
IRRF line. correpy's own per-trade IRRF estimate is ignored; the note's IRRF is
allocated to the sales proportionally to their value, and note fees are allocated
to all trades proportionally to their value (IN RFB 1.585/2015, art. 56, § 4º).
"""

from __future__ import annotations

import io
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from b3_ir.catalog import Catalog, load_catalog
from b3_ir.domain.classify import asset_class_of
from b3_ir.domain.costs import allocate_costs
from b3_ir.domain.models import Operation, Side
from b3_ir.errors import ParseError, UnsupportedOperationError
from b3_ir.money import ZERO

SETTLEMENT_DAYS = 2
FEE_FIELDS = (
    "settlement_fee",
    "registration_fee",
    "term_fee",
    "ana_fee",
    "emoluments",
    "operational_fee",
    "execution",
    "custody_fee",
    "taxes",
    "others",
)
INSTALL_HINT = (
    'leitura de PDF requer o extra opcional: pip install "b3-ir[pdf]" (inclui PyMuPDF, AGPL-3.0)'
)


class _Security(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def ticker(self) -> str | None: ...


class _Transaction(Protocol):
    @property
    def transaction_type(self) -> Any: ...  # correpy TransactionType ("buy" / "sell")
    @property
    def amount(self) -> Decimal: ...
    @property
    def unit_price(self) -> Decimal: ...
    @property
    def security(self) -> _Security: ...


class _Note(Protocol):
    @property
    def reference_id(self) -> int: ...
    @property
    def reference_date(self) -> date: ...
    @property
    def irrf(self) -> Decimal: ...
    @property
    def transactions(self) -> Sequence[_Transaction]: ...


@dataclass
class NoteParseResult:
    operations: list[Operation] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)


def _side(transaction: _Transaction) -> Side:
    value = str(getattr(transaction.transaction_type, "value", transaction.transaction_type))
    if value.lower() == "buy":
        return Side.BUY
    if value.lower() == "sell":
        return Side.SELL
    raise ParseError("nota", f"tipo de negócio desconhecido: {value}")


def _fees(note: _Note) -> Decimal:
    return sum((Decimal(getattr(note, name, ZERO)) for name in FEE_FIELDS), ZERO)


def _allocate_irrf(operations: list[Operation], irrf: Decimal, label: str) -> list[Operation]:
    sells = [i for i, op in enumerate(operations) if op.side is Side.SELL]
    if irrf == ZERO:
        return operations
    if not sells:
        raise ParseError(label, f"IRRF de {irrf} sem vendas na nota")
    total = sum((operations[i].gross_value for i in sells), ZERO)
    result = list(operations)
    remaining = irrf
    for position, index in enumerate(sells):
        op = operations[index]
        share = remaining if position == len(sells) - 1 else irrf * op.gross_value / total
        remaining -= share
        result[index] = replace(op, irrf=share)
    return result


def notes_to_operations(
    notes: Iterable[_Note],
    source: str,
    broker: str | None = None,
    catalog: Catalog | None = None,
) -> NoteParseResult:
    """Convert parsed notes into operations; out-of-scope trades are listed, not guessed.

    Notes usually print the trading name ("BBSEGURIDADE ON NM"), not the ticker; the
    bundled catalog resolves it, and an unknown or ambiguous name is refused.
    """
    catalog = catalog or load_catalog()
    result = NoteParseResult()
    for note in notes:
        label = f"{source}#nota{note.reference_id}"
        day = note.reference_date
        operations: list[Operation] = []
        skipped = False
        for transaction in note.transactions:
            name = transaction.security.name
            ticker = (transaction.security.ticker or catalog.ticker_for_name(name) or "").upper()
            if not ticker:
                result.unsupported.append(f"{label}: ticker não identificado em '{name}'")
                skipped = True
                continue
            try:
                asset_class_of(ticker, catalog.asset_classes)
            except UnsupportedOperationError as exc:
                result.unsupported.append(f"{label}: {exc}")
                skipped = True
                continue
            operations.append(
                Operation(
                    trade_date=day,
                    settlement_date=day + timedelta(days=SETTLEMENT_DAYS),
                    ticker=ticker,
                    side=_side(transaction),
                    quantity=Decimal(transaction.amount),
                    unit_price=Decimal(transaction.unit_price),
                    costs=ZERO,
                    irrf=ZERO,
                    source=label,
                    broker=broker,
                )
            )
        if skipped and operations:
            # Fees and IRRF cover the whole note; allocating them to a subset would
            # misstate costs, so the note is refused as a whole.
            result.unsupported.append(f"{label}: nota com itens fora do escopo ignorada inteira")
            continue
        if not operations:
            continue
        with_costs = allocate_costs(operations, _fees(note))
        result.operations.extend(_allocate_irrf(with_costs, Decimal(note.irrf), label))
    return result


def parse_sinacor(
    path: Path, broker: str | None = None, password: str | None = None
) -> NoteParseResult:
    try:
        from correpy.parsers.brokerage_notes.parser_factory import ParserFactory
    except ImportError as exc:
        raise ParseError(path.name, INSTALL_HINT) from exc
    try:
        content = io.BytesIO(path.read_bytes())
        notes = ParserFactory(brokerage_note=content, password=password).parse()
    except Exception as exc:  # correpy raises assorted errors on unsupported layouts
        raise ParseError(path.name, f"nota não reconhecida pelo correpy: {exc}") from exc
    return notes_to_operations(notes, path.name, broker)
