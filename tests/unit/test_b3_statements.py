"""B3 statements with synthetic spreadsheets in the Área do Investidor layout."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook

from b3_ir.domain.models import EventKind, IncomeKind, Side
from b3_ir.errors import ParseError
from b3_ir.parsers.b3_statements import parse_b3_statement

TRADE_HEADER = [
    "Data do Negócio",
    "Tipo de Movimentação",
    "Mercado",
    "Prazo/Vencimento",
    "Instituição",
    "Código de Negociação",
    "Quantidade",
    "Preço",
    "Valor",
]
MOVEMENT_HEADER = [
    "Entrada/Saída",
    "Data",
    "Movimentação",
    "Produto",
    "Instituição",
    "Quantidade",
    "Preço unitário",
    "Valor da Operação",
]


def xlsx(tmp_path: Path, rows: list[list[object]], name: str = "extrato.xlsx") -> Path:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    for row in rows:
        sheet.append(row)
    path = tmp_path / name
    workbook.save(path)
    return path


def test_trades_statement(tmp_path: Path) -> None:
    path = xlsx(
        tmp_path,
        [
            ["Extrato de negociação"],  # title rows before the header are skipped
            TRADE_HEADER,
            [
                "02/03/2026",
                "Compra",
                "Mercado à Vista",
                "-",
                "XP INVESTIMENTOS",
                "PETR4",
                100,
                30.5,
                3050,
            ],
            [
                datetime(2026, 3, 3),  # noqa: DTZ001 - spreadsheet cells are naive
                "Venda",
                "Mercado à Vista",
                "-",
                "XP",
                "PETR4F",
                7,
                "31,20",
                "218,40",
            ],
            ["04/03/2026", "Compra", "Opções", "-", "XP", "PETRC300", 100, 1.2, 120],
        ],
    )
    result = parse_b3_statement(path)
    buy, sell = result.operations
    assert (buy.trade_date, buy.side, buy.ticker, buy.quantity, buy.unit_price) == (
        date(2026, 3, 2),
        Side.BUY,
        "PETR4",
        Decimal("100"),
        Decimal("30.5"),
    )
    assert buy.broker == "XP INVESTIMENTOS"
    # Fractional-market ticker maps to the same asset.
    assert (sell.ticker, sell.unit_price, sell.costs) == ("PETR4", Decimal("31.20"), 0)
    assert "opcoes" in result.unsupported[0]
    assert "não traz custos" in result.warnings[0]


def test_movements_statement(tmp_path: Path) -> None:
    path = xlsx(
        tmp_path,
        [
            MOVEMENT_HEADER,
            [
                "Credito",
                "10/04/2026",
                "Desdobro",
                "MGLU3 - MAGAZINE LUIZA S/A",
                "XP",
                100,
                "-",
                "-",
            ],
            [
                "Debito",
                "11/04/2026",
                "Grupamento",
                "MGLU3 - MAGAZINE LUIZA S/A",
                "XP",
                150,
                "-",
                "-",
            ],
            [
                "Credito",
                "12/04/2026",
                "Bonificação em Ativos",
                "ITSA4 - ITAUSA S.A.",
                "XP",
                10,
                5.0,
                50,
            ],
            ["Credito", "15/04/2026", "Dividendo", "ITSA4 - ITAUSA S.A.", "XP", 1000, 0.02, 20],
            [
                "Credito",
                "15/04/2026",
                "Juros Sobre Capital Próprio",
                "ITSA4 - ITAUSA S.A.",
                "XP",
                1000,
                0.01,
                8.5,
            ],
            [
                "Credito",
                "16/04/2026",
                "Rendimento - Transferido",
                "HGLG11 - CSHG LOG",
                "XP",
                10,
                1.1,
                11,
            ],
            [
                "Credito",
                "05/03/2026",
                "Transferência - Liquidação",
                "PETR4 - PETROBRAS",
                "XP",
                100,
                30.5,
                3050,
            ],
            [
                "Credito",
                "20/04/2026",
                "Leilão de Fração",
                "ITSA4 - ITAUSA S.A.",
                "XP",
                0.5,
                "-",
                4.2,
            ],
        ],
    )
    result = parse_b3_statement(path)
    assert result.operations == []  # trades come from the Negociação statement only
    split, reverse, bonus = result.events
    assert (split.kind, split.ticker, split.quantity_delta) == (
        EventKind.SPLIT,
        "MGLU3",
        Decimal("100"),
    )
    assert (reverse.kind, reverse.quantity_delta) == (EventKind.REVERSE_SPLIT, Decimal("-150"))
    assert (bonus.kind, bonus.bonus_unit_cost) == (EventKind.BONUS, Decimal("5.0"))
    assert [(i.kind, i.gross) for i in result.income] == [
        (IncomeKind.DIVIDEND, Decimal("20")),
        (IncomeKind.JCP, Decimal("8.5")),
        (IncomeKind.FII_INCOME, Decimal("11")),
    ]
    assert len(result.unsupported) == 1
    assert "leilao de fracao" in result.unsupported[0]


def test_bonus_without_cost_is_refused(tmp_path: Path) -> None:
    path = xlsx(
        tmp_path,
        [
            MOVEMENT_HEADER,
            ["Credito", "12/04/2026", "Bonificação em Ativos", "ITSA4", "XP", 10, "-", "-"],
        ],
    )
    result = parse_b3_statement(path)
    assert result.events == []
    assert "sem custo atribuído" in result.unsupported[0]


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([["qualquer", "coisa"]], "cabeçalho"),
        (
            [
                TRADE_HEADER,
                ["32/13/2026", "Compra", "Mercado à Vista", "-", "XP", "PETR4", 1, 1, 1],
            ],
            "linha 2",
        ),
        (
            [TRADE_HEADER, ["02/03/2026", "Troca", "Mercado à Vista", "-", "XP", "PETR4", 1, 1, 1]],
            "desconhecido",
        ),
    ],
)
def test_invalid_statements(tmp_path: Path, rows: list[list[object]], message: str) -> None:
    with pytest.raises(ParseError, match=message):
        parse_b3_statement(xlsx(tmp_path, rows))


def test_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "x.xlsx"
    path.write_bytes(b"PK")
    with pytest.raises(ParseError, match="planilha inválida"):
        parse_b3_statement(path)
