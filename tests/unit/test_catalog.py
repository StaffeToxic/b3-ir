import csv
from importlib.resources import files

import pytest

from b3_ir.catalog import Catalog, load_catalog, normalize_name
from b3_ir.domain.models import AssetClass


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("BBSEGURIDADE ON NM", "BBSEGURIDADE ON NM"),
        ("BRASIL ON EJ NM", "BRASIL ON NM"),
        ("MOVIDA ON ATZ NM", "MOVIDA ON NM"),
        ("FII HGLG PAX CI ER", "FII HGLG PAX"),
        ("klabin s.a unt n2", "KLABIN SA UNT N2"),
    ],
)
def test_normalize_name(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected


@pytest.mark.parametrize(
    ("name", "ticker"),
    [
        # Names printed in a real SINACOR note (correpy fixture b3_one_page.pdf, 2022).
        ("BBSEGURIDADE ON NM", "BBSE3"),
        ("BR PARTNERS UNT N2", "BRBI11"),
        ("BRASIL ON NM", "BBAS3"),
        ("ENERGIAS BR ON NM", "ENBR3"),
        ("ENGIE BRASIL ON NM", "EGIE3"),
        ("KLABIN S/A UNT N2", "KLBN11"),
        ("SUL AMERICA UNT N2", "SULA11"),
        ("BLAU ON NM", "BLAU3"),
        ("MOVIDA ON NM", "MOVI3"),
        ("PETROBRAS PN N2", "PETR4"),
    ],
)
def test_note_names_resolve_to_tickers(name: str, ticker: str) -> None:
    assert load_catalog().ticker_for_name(name) == ticker


def test_unknown_or_ambiguous_names_are_not_guessed() -> None:
    catalog = Catalog({}, {"FII KINEA": frozenset({"KNRI11", "KNCR11"})})
    assert catalog.ticker_for_name("FII KINEA CI") is None
    assert catalog.ticker_for_name("NAO EXISTE ON") is None


@pytest.mark.parametrize(
    ("ticker", "expected"),
    [
        ("PETR4", AssetClass.STOCK),
        ("TAEE11", AssetClass.STOCK),
        ("HGLG11", AssetClass.FII),
        ("BOVA11", AssetClass.ETF),
    ],
)
def test_asset_classes_from_bdi_codes(ticker: str, expected: AssetClass) -> None:
    assert load_catalog().asset_classes[ticker] is expected


def test_bundled_table_has_no_bdrs_or_fractional_lots() -> None:
    text = files("b3_ir.data").joinpath("ativos.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(text.splitlines(), delimiter=";"))
    assert len(rows) > 3000
    assert not [r for r in rows if r["especificacao"].startswith("DR")]
    assert not [r for r in rows if r["ticker"].endswith("F")]
    assert {r["classe"] for r in rows} == {"acao", "fii", "etf"}
