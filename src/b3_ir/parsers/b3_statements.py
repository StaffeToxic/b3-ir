"""B3 Área do Investidor statements in XLSX (FR-003, research D-R4-3).

Two exports are read:

- **Negociação**: one row per trade, with the trade date. Source of operations.
  The statement has no brokerage costs, so operations come with zero costs and a
  warning; brokerage notes, when present, replace them (see dedup.py).
- **Movimentação**: custody movements. Source of corporate events (split, reverse
  split, bonus) and income (dividends, JCP, FII income). Its "Transferência -
  Liquidação" rows repeat the trades with the settlement date, so they are ignored
  to avoid double counting with the wrong date.

The type of statement is detected from the header row. Column names are matched
accent- and case-insensitively against known aliases (labels as listed in MonnaIA's
movement catalog, research/r6-prior-art.md).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from b3_ir.domain.models import CorporateEvent, EventKind, IncomeEntry, IncomeKind, Operation, Side
from b3_ir.errors import ParseError
from b3_ir.money import ZERO, parse_brl, to_decimal

SETTLEMENT_DAYS = 2

TRADE_COLUMNS = {
    "data": ("data do negocio", "data negocio", "data"),
    "tipo": ("tipo de movimentacao", "tipo de operacao", "compra/venda", "tipo"),
    "mercado": ("mercado",),
    "instituicao": ("instituicao", "corretora"),
    "ticker": ("codigo de negociacao", "codigo", "ticker", "ativo"),
    "quantidade": ("quantidade", "qtd", "quant"),
    "preco": ("preco", "preco unitario"),
}
MOVEMENT_COLUMNS = {
    "direcao": ("entrada/saida", "entrada / saida", "credito/debito"),
    "data": ("data", "data da movimentacao"),
    "movimentacao": ("movimentacao", "tipo de movimentacao"),
    "produto": ("produto", "ativo"),
    "instituicao": ("instituicao", "corretora"),
    "quantidade": ("quantidade", "qtd"),
    "preco": ("preco unitario", "preco"),
    "valor": ("valor da operacao", "valor"),
}

_SPOT_MARKETS = ("mercado a vista", "a vista", "vista", "")
_EVENT_LABELS = {
    "desdobro": EventKind.SPLIT,
    "desdobramento": EventKind.SPLIT,
    "grupamento": EventKind.REVERSE_SPLIT,
    "agrupamento": EventKind.REVERSE_SPLIT,
    "bonificacao em ativos": EventKind.BONUS,
    "bonificacao": EventKind.BONUS,
}
_INCOME_LABELS = {
    "dividendo": IncomeKind.DIVIDEND,
    "juros sobre capital proprio": IncomeKind.JCP,
    "rendimento": IncomeKind.FII_INCOME,
}
_IGNORED_LABELS = ("transferencia - liquidacao", "compra / venda", "compra/venda", "atualizacao")


def _key(text: object) -> str:
    """Lowercase, accent-free, single-spaced, without the ' - transferido' suffix."""
    raw = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    cleaned = " ".join(raw.lower().replace(".", "").split())
    return cleaned.removesuffix(" - transferido")


@dataclass
class StatementParseResult:
    operations: list[Operation] = field(default_factory=list)
    events: list[CorporateEvent] = field(default_factory=list)
    income: list[IncomeEntry] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _find_columns(header: Sequence[object], aliases: dict[str, tuple[str, ...]]) -> dict[str, int]:
    keys = [_key(cell) for cell in header]
    found: dict[str, int] = {}
    for name, options in aliases.items():
        for option in options:
            if option in keys:
                found[name] = keys.index(option)
                break
    return found


def _date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()  # noqa: DTZ007 - dates only
        except ValueError:
            continue
    raise ValueError(f"data inválida: {text!r}")


def _number(value: object) -> Decimal | None:
    """Numbers come as int, float (openpyxl) or text like 'R$ 1.234,56'; '-' means empty."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        # Spreadsheet cells hold binary floats; go through repr to keep the typed digits.
        return Decimal(repr(value))
    text = str(value).strip()
    if text in {"", "-"}:
        return None
    return parse_brl(text) if "," in text else to_decimal(text.replace("R$", "").strip())


def _required(value: object, name: str) -> Decimal:
    number = _number(value)
    if number is None:
        raise ValueError(f"{name} vazio")
    return number


def _ticker(product: object) -> str:
    """'PETR4 - PETROLEO BRASILEIRO S.A.' -> 'PETR4'."""
    return str(product or "").split(" - ")[0].strip().upper()


def _rows(path: Path) -> Iterator[tuple[int, list[object]]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - openpyxl is a runtime dependency
        raise ParseError(path.name, "openpyxl não instalado") from exc
    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:  # openpyxl raises several types on corrupt files
        raise ParseError(path.name, f"planilha inválida: {exc}") from exc
    try:
        sheet = workbook.worksheets[0]
        for index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            yield index, list(row)
    finally:
        workbook.close()


def parse_b3_statement(path: Path) -> StatementParseResult:
    rows = list(_rows(path))
    for position, (_, header) in enumerate(rows[:20]):
        trade_cols = _find_columns(header, TRADE_COLUMNS)
        if {"data", "tipo", "ticker", "quantidade", "preco"} <= trade_cols.keys():
            return _parse_trades(path, rows[position + 1 :], trade_cols)
        movement_cols = _find_columns(header, MOVEMENT_COLUMNS)
        if {"direcao", "data", "movimentacao", "produto", "quantidade"} <= movement_cols.keys():
            return _parse_movements(path, rows[position + 1 :], movement_cols)
    raise ParseError(
        path.name, "cabeçalho de extrato da B3 (Negociação ou Movimentação) não encontrado"
    )


def _cell(row: list[object], cols: dict[str, int], name: str) -> Any:
    index = cols.get(name)
    return row[index] if index is not None and index < len(row) else None


def _parse_trades(
    path: Path, rows: list[tuple[int, list[object]]], cols: dict[str, int]
) -> StatementParseResult:
    result = StatementParseResult()
    for line, row in rows:
        if not any(cell not in (None, "") for cell in row):
            continue
        label = f"{path.name}#linha{line}"
        try:
            market = _key(_cell(row, cols, "mercado"))
            if market not in _SPOT_MARKETS:
                result.unsupported.append(f"{label}: mercado '{market}' fora do escopo")
                continue
            kind = _key(_cell(row, cols, "tipo"))
            side = {"compra": Side.BUY, "venda": Side.SELL}.get(kind)
            if side is None:
                raise ValueError(f"tipo de negócio desconhecido: {kind!r}")
            day = _date(_cell(row, cols, "data"))
            broker = str(_cell(row, cols, "instituicao") or "").strip() or None
            result.operations.append(
                Operation(
                    trade_date=day,
                    settlement_date=day + timedelta(days=SETTLEMENT_DAYS),
                    ticker=_ticker(_cell(row, cols, "ticker")).removesuffix("F"),
                    side=side,
                    quantity=_required(_cell(row, cols, "quantidade"), "quantidade"),
                    unit_price=_required(_cell(row, cols, "preco"), "preço"),
                    costs=ZERO,
                    irrf=ZERO,
                    source=label,
                    broker=broker,
                )
            )
        except (ValueError, InvalidOperation, TypeError) as exc:
            raise ParseError(path.name, f"linha {line}: {exc}") from exc
    if result.operations:
        result.warnings.append(
            f"{path.name}: o extrato de negociação não traz custos nem IRRF; "
            "use as notas de corretagem para o custo exato"
        )
    return result


def _parse_movements(
    path: Path, rows: list[tuple[int, list[object]]], cols: dict[str, int]
) -> StatementParseResult:
    result = StatementParseResult()
    for line, row in rows:
        if not any(cell not in (None, "") for cell in row):
            continue
        label = f"{path.name}#linha{line}"
        movement = _key(_cell(row, cols, "movimentacao"))
        if movement in _IGNORED_LABELS:
            continue
        try:
            day = _date(_cell(row, cols, "data"))
            ticker = _ticker(_cell(row, cols, "produto"))
            debit = _key(_cell(row, cols, "direcao")).startswith(("debito", "saida"))
            if movement in _EVENT_LABELS:
                _event(result, label, day, ticker, movement, debit, row, cols)
            elif movement in _INCOME_LABELS:
                gross = _required(_cell(row, cols, "valor"), "valor")
                result.income.append(
                    IncomeEntry(day, ticker, _INCOME_LABELS[movement], gross, ZERO, label)
                )
            else:
                result.unsupported.append(f"{label}: movimentação '{movement}' não suportada")
        except (ValueError, InvalidOperation, TypeError) as exc:
            raise ParseError(path.name, f"linha {line}: {exc}") from exc
    return result


def _event(
    result: StatementParseResult,
    label: str,
    day: date,
    ticker: str,
    movement: str,
    debit: bool,
    row: list[object],
    cols: dict[str, int],
) -> None:
    kind = _EVENT_LABELS[movement]
    quantity = _required(_cell(row, cols, "quantidade"), "quantidade")
    delta = -quantity if debit or kind is EventKind.REVERSE_SPLIT else quantity
    if kind is EventKind.REVERSE_SPLIT and not debit and quantity > ZERO:
        # A reverse split in the statement is a debit; a credit row is unexpected.
        result.unsupported.append(f"{label}: grupamento lançado como crédito")
        return
    if kind is EventKind.SPLIT and debit:
        result.unsupported.append(f"{label}: desdobro lançado como débito")
        return
    bonus_cost: Decimal | None = None
    if kind is EventKind.BONUS:
        bonus_cost = _number(_cell(row, cols, "preco"))
        if not bonus_cost:
            # The cost per bonus share is set by the company (IN 1.585, art. 58, § 1º)
            # and is not always in the statement; refusing beats assuming zero.
            result.unsupported.append(
                f"{label}: bonificação de {ticker} sem custo atribuído; "
                "informe-o no CSV manual (tipo bonificacao, coluna preco)"
            )
            return
    result.events.append(CorporateEvent(day, ticker, kind, delta, bonus_cost, label))
