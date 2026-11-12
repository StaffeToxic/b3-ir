"""Local web interface: security properties and parity with the CLI (spec 002)."""

import base64
import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

from b3_ir.errors import B3IRError
from b3_ir.web.server import TOKEN_HEADER, make_server, safe_relative_path, url_of

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "operacoes.csv"


@pytest.fixture
def server() -> Iterator[Any]:
    srv = make_server()
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def base(srv: Any) -> str:
    host, port = srv.server_address[:2]
    return f"http://{host}:{port}"


def post(srv: Any, body: object, token: str | None) -> tuple[int, dict[str, Any]]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers[TOKEN_HEADER] = token
    request = urllib.request.Request(
        base(srv) + "/api/analisar", json.dumps(body).encode(), headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def example_body() -> dict[str, Any]:
    data = base64.b64encode(EXAMPLE.read_bytes()).decode()
    return {"arquivos": [{"caminho": "exemplo/operacoes.csv", "base64": data}]}


def test_refuses_non_loopback_host() -> None:
    with pytest.raises(B3IRError, match="próprio computador"):
        make_server(host="0.0.0.0")


def test_page_requires_token(server: Any) -> None:
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(base(server) + "/")
    assert exc.value.code == 403
    with urllib.request.urlopen(url_of(server)) as response:
        page = response.read().decode()
        assert server.token in page
        assert "não é consultoria tributária" in page  # FR-W06
        assert "default-src 'none'" in response.headers["Content-Security-Policy"]


def test_api_requires_token(server: Any) -> None:
    status, body = post(server, example_body(), token=None)
    assert (status, body["erro"]) == (403, "token ausente ou inválido")


def test_api_matches_cli_results(server: Any) -> None:
    status, result = post(server, example_body(), server.token)
    assert status == 200
    assert result["anos"] == [2026]
    may = next(m for m in result["mensal"]["2026"] if m["month"] == "2026-05")
    assert may["darf"]["amount"] == "91.81"
    assert may["darf"]["due_date"] == "2026-06-30"
    itsa = next(p for p in result["anual"]["2026"]["assets"] if p["ticker"] == "ITSA4")
    assert Decimal(itsa["cost"]) == Decimal("573")
    assert [p["ticker"] for p in result["posicoes"]] == ["ITSA4"]


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({}, "arquivos"),
        ({"arquivos": []}, "nenhum arquivo"),
        ({"arquivos": [{"caminho": "a.csv", "base64": "%%%"}]}, "base64"),
    ],
)
def test_api_rejects_bad_requests(server: Any, body: object, message: str) -> None:
    status, result = post(server, body, server.token)
    assert status == 400
    assert message in result["erro"]


def test_unprocessable_data_returns_422(server: Any) -> None:
    csv = "data;tipo;ticker;quantidade;preco\n2026-01-05;venda;PETR4;10;30\n"
    body = {"arquivos": [{"caminho": "x.csv", "base64": base64.b64encode(csv.encode()).decode()}]}
    status, result = post(server, body, server.token)
    assert status == 422
    assert "descoberto" in result["erro"]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("nota.pdf", "upload/nota.pdf"),
        ("xp/nota.pdf", "xp/nota.pdf"),
        ("../../etc/passwd", "etc/passwd"),
        ("C:\\Users\\x\\notas\\clear\\n.pdf", "notas/clear/n.pdf"),
        ("a/b/c/d/e.csv", "c/d/e.csv"),
        ("xp/<script>.pdf", "xp/_script_.pdf"),
    ],
)
def test_safe_relative_path(name: str, expected: str) -> None:
    path = safe_relative_path(name)
    assert path == PurePosixPath(expected)
    assert ".." not in path.parts
