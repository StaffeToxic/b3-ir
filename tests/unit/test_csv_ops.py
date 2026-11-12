from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from b3_ir.domain.models import EventKind, Side
from b3_ir.errors import ParseError
from b3_ir.parsers.csv_ops import parse_operations_csv


def write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "ops.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_parses_operations_and_events(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "data;tipo;ticker;quantidade;preco;custos;irrf\n"
        "05/01/2026;compra;itsa4;1000;10,05;5,00;\n"
        "2026-02-10;venda;ITSA4;400;12.00;2;0,24\n"
        "2026-03-01;grupamento;ITSA4;100;;;\n"
        "2026-04-01;bonificacao;ITSA4;10;5,00;;\n"
        ";;;;;;\n",
    )
    result = parse_operations_csv(path)
    buy, sell = result.operations
    assert (buy.trade_date, buy.ticker, buy.side, buy.quantity, buy.unit_price) == (
        date(2026, 1, 5),
        "ITSA4",
        Side.BUY,
        Decimal("1000"),
        Decimal("10.05"),
    )
    assert (sell.costs, sell.irrf, sell.source) == (Decimal("2"), Decimal("0.24"), "ops.csv#linha3")
    reverse, bonus = result.events
    assert (reverse.kind, reverse.quantity_delta) == (EventKind.REVERSE_SPLIT, Decimal("-100"))
    assert (bonus.kind, bonus.bonus_unit_cost) == (EventKind.BONUS, Decimal("5.00"))


def test_comma_separated_file(tmp_path: Path) -> None:
    path = write(tmp_path, "data,tipo,ticker,quantidade,preco\n2026-01-05,compra,PETR4,10,30.5\n")
    assert parse_operations_csv(path).operations[0].unit_price == Decimal("30.5")


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("data;tipo;ticker\n", "colunas ausentes"),
        ("", "colunas ausentes"),
        ("data;tipo;ticker;quantidade;preco\n2026-13-01;compra;PETR4;1;1\n", "linha 2"),
        ("data;tipo;ticker;quantidade;preco\n2026-01-01;troca;PETR4;1;1\n", "tipo desconhecido"),
        ("data;tipo;ticker;quantidade;preco\n2026-01-01;compra;PETR4;1;\n", "obrigatório"),
    ],
)
def test_invalid_files(tmp_path: Path, content: str, message: str) -> None:
    with pytest.raises(ParseError, match=message):
        parse_operations_csv(write(tmp_path, content))
