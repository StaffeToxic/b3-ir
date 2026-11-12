"""Build src/b3_ir/data/ativos.csv from B3's COTAHIST historical quotes.

COTAHIST is B3's public fixed-width file of daily quotes. Each spot-market line
(TPMERC 010) carries the ticker (CODNEG), the BDI code, the trading name (NOMRES)
and the specification (ESPECI), which is exactly what brokerage notes print
instead of the ticker ("BBSEGURIDADE ON NM" -> BBSE3).

BDI codes kept (research D-R4-2): 02, 07, 08 = stocks (standard lot, including
companies in judicial or extrajudicial recovery); 12 = FII; 14 = ETF. Everything
else (BDRs, rights, Fiagro, debentures) is out of the MVP scope and left out, so
those tickers are refused downstream instead of misclassified.

Dev tool (network). Usage:
    python scripts/atualizar_ativos.py 2022 2023 2024 2025 2026
"""

from __future__ import annotations

import argparse
import csv
import io
import urllib.request
import zipfile
from pathlib import Path

URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"
OUT = Path(__file__).resolve().parents[1] / "src" / "b3_ir" / "data" / "ativos.csv"
CLASSES = {"02": "acao", "07": "acao", "08": "acao", "12": "fii", "14": "etf"}

Row = tuple[str, str, str, str]  # (ticker, class, trading name, specification)


def download(year: int) -> bytes:
    request = urllib.request.Request(URL.format(year=year), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=600) as response:
        data: bytes = response.read()
    return data


def read_lines(zipped: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(zipped)) as archive:
        name = archive.namelist()[0]
        return archive.read(name).decode("latin-1").splitlines()


def collect(lines: list[str], rows: dict[Row, str]) -> None:
    """Record every (ticker, class, name, specification) seen, with its last quote date.

    Trading names change over time and old notes print old names, so every
    combination is kept, not only the latest one.
    """
    for line in lines:
        if not line.startswith("01") or line[24:27] != "010":
            continue
        ticker = line[12:24].strip()
        asset_class = CLASSES.get(line[10:12])
        spec = " ".join(line[39:49].split())
        # Fractional lots (suffix F) and BDRs are out of scope; older files list some
        # BDRs under BDI 02, so they are also recognized by the DR* specification.
        if asset_class is None or ticker.endswith("F") or spec.startswith("DR"):
            continue
        key = (ticker, asset_class, line[27:39].strip(), spec)
        day = line[2:10]
        if rows.get(key, "") < day:
            rows[key] = day


def write(rows: dict[Row, str], out: Path = OUT) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", lineterminator="\n")
        writer.writerow(["ticker", "classe", "nome_pregao", "especificacao", "ultima_cotacao"])
        for key in sorted(rows):
            day = rows[key]
            writer.writerow([*key, f"{day[:4]}-{day[4:6]}-{day[6:]}"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("anos", nargs="+", type=int)
    args = parser.parse_args()
    rows: dict[Row, str] = {}
    for year in sorted(args.anos):
        collect(read_lines(download(year)), rows)
        print(f"{year}: {len(rows)} combinações acumuladas")
    write(rows)
    print(f"{OUT}: {len(rows)} linhas")


if __name__ == "__main__":
    main()
