"""Constitution II, IV and V checked statically over the source tree."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "b3_ir"
DOMAIN = SRC / "domain"

NETWORK_MODULES = {"socket", "urllib", "http", "requests", "httpx", "aiohttp", "ftplib", "smtplib"}
IO_MODULES = {"pathlib", "os", "io", "shutil", "pdfplumber", "openpyxl", "csv", "json"}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def py_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


@pytest.mark.parametrize("path", py_files(SRC), ids=lambda p: p.name)
def test_no_network_imports(path: Path) -> None:
    assert not imported_roots(path) & NETWORK_MODULES


@pytest.mark.parametrize("path", py_files(DOMAIN), ids=lambda p: p.name)
def test_domain_has_no_io_imports(path: Path) -> None:
    assert not imported_roots(path) & IO_MODULES


@pytest.mark.parametrize("path", py_files(DOMAIN), ids=lambda p: p.name)
def test_domain_does_not_import_adapters(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "b3_ir.parsers" not in text
    assert "b3_ir.report" not in text
    assert "b3_ir.cli" not in text


@pytest.mark.parametrize("path", py_files(DOMAIN), ids=lambda p: p.name)
def test_domain_never_uses_float(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float), f"float literal em {path.name}"
        if isinstance(node, ast.Name):
            assert node.id != "float", f"uso de float em {path.name}"
