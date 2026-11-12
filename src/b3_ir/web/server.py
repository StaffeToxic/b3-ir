"""Local web interface (specs/002-interface-web).

Serves one static page on the loopback interface only. The browser sends the files
as base64 JSON; they are written to a temporary folder (kept folder structure, so a
PDF's parent folder still names the broker), processed by the same code as the CLI,
and deleted right after. No outbound request is ever made (Constitution IV).
"""

from __future__ import annotations

import base64
import binascii
import contextlib
import ipaddress
import json
import os
import re
import secrets
import tempfile
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse

from b3_ir import __version__
from b3_ir.domain.annual import build_annual_report
from b3_ir.domain.assessment import CarryState, assess_year
from b3_ir.domain.positions import build_positions
from b3_ir.errors import B3IRError
from b3_ir.inputs import load_inputs
from b3_ir.report.json_out import to_jsonable

MAX_BODY = 50 * 1024 * 1024
TOKEN_HEADER = "X-B3IR-Token"
ROOT_FOLDER = "upload"
_SAFE = re.compile(r"[^\w.\- ]", re.UNICODE)


def token_path() -> Path:
    """Per-user file that keeps the session token across restarts."""
    base = os.environ.get("APPDATA") or os.environ.get("XDG_CONFIG_HOME")
    return Path(base or Path.home() / ".config") / "b3-ir" / "web-token"


def load_or_create_token(path: Path | None = None) -> str:
    """Reuse the saved token so a tab opened before a restart keeps working."""
    path = path or token_path()
    try:
        token = path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeDecodeError):
        token = ""
    if not re.fullmatch(r"[\w-]{32,}", token):
        token = secrets.token_urlsafe(24)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(token, encoding="ascii")
        with contextlib.suppress(OSError):  # permissions are best effort on Windows
            path.chmod(0o600)
    return token


def safe_relative_path(name: str) -> PurePosixPath:
    """Keep at most the last three path parts, without traversal or odd characters."""
    parts = [p for p in re.split(r"[\\/]", name) if p not in {"", ".", ".."}]
    cleaned = [_SAFE.sub("_", p).strip(" .") or "_" for p in parts[-3:]]
    if not cleaned:
        raise ValueError("nome de arquivo vazio")
    if len(cleaned) == 1:
        cleaned.insert(0, ROOT_FOLDER)
    return PurePosixPath(*cleaned)


def analyze_files(uploads: list[tuple[str, bytes]]) -> dict[str, Any]:
    """Run the full pipeline on uploaded files and return a JSON-ready result."""
    with tempfile.TemporaryDirectory(prefix="b3ir-") as tmp:
        root = Path(tmp)
        for name, content in uploads:
            target = root / safe_relative_path(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        inputs = load_inputs([root])
    operations = inputs.classified()
    ledger = build_positions(operations, inputs.events)
    years = sorted(
        {op.trade_date.year for op in operations}
        | {item.payment_date.year for item in inputs.income}
    )
    monthly: dict[str, Any] = {}
    annual: dict[str, Any] = {}
    carry: CarryState | None = None
    for year in years:
        months, carry = assess_year(ledger.realized, year, carry)
        monthly[str(year)] = months
        annual[str(year)] = build_annual_report(operations, inputs.events, inputs.income, year)
    result = to_jsonable(
        {
            "anos": years,
            "posicoes": ledger.open_positions(),
            "mensal": monthly,
            "anual": annual,
            "avisos": inputs.warnings,
            "nao_suportados": inputs.unsupported,
            "ignorados": inputs.ignored,
        }
    )
    assert isinstance(result, dict)
    return result


def _decode_uploads(payload: object) -> list[tuple[str, bytes]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("arquivos"), list):
        raise ValueError("corpo deve ter a lista 'arquivos'")
    if payload.get("aceite_termo") is not True:
        # The disclaimer must be accepted on every use (spec 002, FR-W06).
        raise ValueError("é preciso aceitar o termo de isenção de responsabilidade")
    uploads = []
    for item in payload["arquivos"]:
        if not isinstance(item, dict):
            raise ValueError("arquivo inválido")
        name, data = item.get("caminho"), item.get("base64")
        if not isinstance(name, str) or not isinstance(data, str):
            raise ValueError("arquivo sem 'caminho' ou 'base64'")
        try:
            uploads.append((name, base64.b64decode(data, validate=True)))
        except binascii.Error as exc:
            raise ValueError(f"base64 inválido em {name}") from exc
    if not uploads:
        raise ValueError("nenhum arquivo enviado")
    return uploads


class _Handler(BaseHTTPRequestHandler):
    server: _Server
    server_version = f"b3-ir/{__version__}"

    def log_message(self, format: str, *args: Any) -> None:
        """Silent: request lines would expose file names and the token."""

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
            "img-src data:; connect-src 'self'; form-action 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: HTTPStatus, data: object) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode(), "application/json")

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path != "/":
            self._json(HTTPStatus.NOT_FOUND, {"erro": "não encontrado"})
            return
        token = parse_qs(url.query).get("t", [""])[0]
        if not secrets.compare_digest(token, self.server.token):
            message = "Abra o endereço completo mostrado no terminal (com ?t=...)."
            self._send(HTTPStatus.FORBIDDEN, message.encode(), "text/plain; charset=utf-8")
            return
        page = self.server.page.replace("__B3IR_TOKEN__", self.server.token)
        self._send(HTTPStatus.OK, page.encode(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/analisar":
            self._json(HTTPStatus.NOT_FOUND, {"erro": "não encontrado"})
            return
        if not secrets.compare_digest(self.headers.get(TOKEN_HEADER, ""), self.server.token):
            self._json(HTTPStatus.FORBIDDEN, {"erro": "token ausente ou inválido"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"erro": "arquivos acima de 50 MB"})
            return
        try:
            uploads = _decode_uploads(json.loads(self.rfile.read(length) or b"null"))
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"erro": str(exc)})
            return
        try:
            self._json(HTTPStatus.OK, analyze_files(uploads))
        except B3IRError as exc:
            self._json(HTTPStatus.UNPROCESSABLE_ENTITY, {"erro": str(exc)})


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], token: str, page: str) -> None:
        super().__init__(address, _Handler)
        self.token = token
        self.page = page


def make_server(port: int = 0, host: str = "127.0.0.1", token: str | None = None) -> _Server:
    """Create the server; only loopback addresses are accepted (FR-W01)."""
    if not ipaddress.ip_address(host).is_loopback:
        raise B3IRError(f"a interface só escuta no próprio computador, não em {host}")
    page = files("b3_ir.web").joinpath("static/index.html").read_text(encoding="utf-8")
    return _Server((host, port), token or secrets.token_urlsafe(24), page)


def url_of(server: _Server) -> str:
    host, port = server.server_address[:2]
    return f"http://{host!s}:{port}/?t={server.token}"


def serve(port: int = 0, open_browser: bool = True) -> None:
    server = make_server(port, token=load_or_create_token())
    url = url_of(server)
    print(f"b3-ir rodando em {url}")
    print("Os arquivos ficam só neste computador. Ctrl+C para encerrar.")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nencerrado")
    finally:
        server.server_close()
