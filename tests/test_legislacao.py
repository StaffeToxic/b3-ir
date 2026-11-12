"""Traceability: every norm cited in rules.py is versioned in legislacao/ (Constitution I)."""

import re
from pathlib import Path

import pytest

from b3_ir import rules

ROOT = Path(__file__).resolve().parents[1] / "legislacao"
NORMS = sorted(p for p in ROOT.rglob("*.md") if p.name != "README.md")
REQUIRED = (
    "schema_versao",
    "id",
    "tipo",
    "titulo",
    "orgao",
    "numero",
    "data",
    "versao_texto",
    "ementa",
    "fonte",
    "sha256_fonte",
    "formato_fonte",
    "baixado_em",
)
CITATION = re.compile(r"\b(Lei|IN RFB) (\d[\d.]*)/(\d{4})")


def front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path.name
    block = text.split("---\n", 2)[1]
    return dict(line.split(": ", 1) for line in block.splitlines())


def cited_ids() -> set[str]:
    ids = set()
    for versions in rules.RULES.values():
        for rule in versions:
            for kind, number, year in CITATION.findall(rule.source):
                prefix = "lei" if kind == "Lei" else "in-rfb"
                ids.add(f"{prefix}-{number.replace('.', '')}-{year}")
    return ids


def test_there_are_norms() -> None:
    assert len(NORMS) >= 7


@pytest.mark.parametrize("path", NORMS, ids=lambda p: p.stem)
def test_front_matter_is_complete(path: Path) -> None:
    meta = front_matter(path)
    assert all(key in meta for key in REQUIRED), set(REQUIRED) - set(meta)
    assert meta["id"].strip('"') == path.stem
    assert re.fullmatch(r'"[0-9a-f]{64}"', meta["sha256_fonte"])
    assert meta["data"].strip('"')[:4] == path.parent.name


@pytest.mark.parametrize("norm_id", sorted(cited_ids()))
def test_every_cited_norm_is_versioned(norm_id: str) -> None:
    assert any(p.stem == norm_id for p in NORMS), f"{norm_id} ausente em legislacao/"


@pytest.mark.parametrize("path", NORMS, ids=lambda p: p.stem)
def test_every_norm_is_listed_in_the_index(path: Path) -> None:
    index = (ROOT / "README.md").read_text(encoding="utf-8")
    assert path.relative_to(ROOT).as_posix() in index
