"""Download the official texts cited in docs/regras-fiscais.md and publish them as Markdown.

Follows the layout of github.com/StaffeToxic/normas-cvm: one file per norm under
``legislacao/<orgao>/<familia>/<ano>/<id>.md`` with YAML front matter (source URL,
SHA-256 of the downloaded bytes, download date) and the current consolidated text.

Sources: Planalto (laws, compiled text) and the Receita Federal normative API
(normasinternet2). Struck-through passages (revoked wording) are dropped, so the
Markdown is the text in force on the download date; annotations such as
"(Redação dada pela Lei ...)" are kept.

Dev tool, not part of the package: it is the only code in the repo that touches
the network (Constitution IV applies to the library at runtime).

Usage: python scripts/atualizar_legislacao.py [--saida legislacao]
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.request
from dataclasses import dataclass, replace
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (b3-ir legislacao; +https://github.com/StaffeToxic/b3-ir)"
SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Norma:
    id: str
    tipo: str
    numero: str
    data: str
    orgao: str
    pasta: str
    titulo: str
    ementa: str
    fonte: str
    formato: str  # "planalto-html" or "rfb-api"


NORMAS = (
    Norma(
        "lei-8668-1993",
        "Lei",
        "8.668",
        "1993-06-25",
        "Presidência da República",
        "federal/leis",
        "Lei nº 8.668, de 25 de junho de 1993",
        "Dispõe sobre a constituição e o regime tributário dos Fundos de Investimento "
        "Imobiliário e dá outras providências.",
        "https://www.planalto.gov.br/ccivil_03/leis/l8668.htm",
        "planalto-html",
    ),
    Norma(
        "lei-8981-1995",
        "Lei",
        "8.981",
        "1995-01-20",
        "Presidência da República",
        "federal/leis",
        "Lei nº 8.981, de 20 de janeiro de 1995",
        "Altera a legislação tributária Federal e dá outras providências.",
        "https://www.planalto.gov.br/ccivil_03/leis/l8981.htm",
        "planalto-html",
    ),
    Norma(
        "lei-9249-1995",
        "Lei",
        "9.249",
        "1995-12-26",
        "Presidência da República",
        "federal/leis",
        "Lei nº 9.249, de 26 de dezembro de 1995",
        "",
        "https://www.planalto.gov.br/ccivil_03/leis/l9249.htm",
        "planalto-html",
    ),
    Norma(
        "lei-9250-1995",
        "Lei",
        "9.250",
        "1995-12-26",
        "Presidência da República",
        "federal/leis",
        "Lei nº 9.250, de 26 de dezembro de 1995",
        "",
        "https://www.planalto.gov.br/ccivil_03/leis/l9250.htm",
        "planalto-html",
    ),
    Norma(
        "lei-9430-1996",
        "Lei",
        "9.430",
        "1996-12-27",
        "Presidência da República",
        "federal/leis",
        "Lei nº 9.430, de 27 de dezembro de 1996",
        "Dispõe sobre a legislação tributária federal, as contribuições para a seguridade "
        "social, o processo administrativo de consulta e dá outras providências.",
        "https://www.planalto.gov.br/ccivil_03/leis/l9430.htm",
        "planalto-html",
    ),
    Norma(
        "lei-9779-1999",
        "Lei",
        "9.779",
        "1999-01-19",
        "Presidência da República",
        "federal/leis",
        "Lei nº 9.779, de 19 de janeiro de 1999",
        "",
        "https://www.planalto.gov.br/ccivil_03/leis/l9779.htm",
        "planalto-html",
    ),
    Norma(
        "lei-9959-2000",
        "Lei",
        "9.959",
        "2000-01-27",
        "Presidência da República",
        "federal/leis",
        "Lei nº 9.959, de 27 de janeiro de 2000",
        "Altera a legislação tributária federal e dá outras providências.",
        "https://www.planalto.gov.br/ccivil_03/leis/l9959.htm",
        "planalto-html",
    ),
    Norma(
        "lei-11033-2004",
        "Lei",
        "11.033",
        "2004-12-21",
        "Presidência da República",
        "federal/leis",
        "Lei nº 11.033, de 21 de dezembro de 2004",
        "Altera a tributação do mercado financeiro e de capitais; institui o Regime "
        "Tributário para Incentivo à Modernização e à Ampliação da Estrutura Portuária "
        "- REPORTO; e dá outras providências.",
        "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l11033.htm",
        "planalto-html",
    ),
    Norma(
        "lei-15270-2025",
        "Lei",
        "15.270",
        "2025-11-26",
        "Presidência da República",
        "federal/leis",
        "Lei nº 15.270, de 26 de novembro de 2025",
        "Altera a legislação do Imposto sobre a Renda das Pessoas Físicas, inclusive a "
        "tributação mensal e anual de altas rendas.",
        "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/L15270.htm",
        "planalto-html",
    ),
    Norma(
        "lcp-224-2025",
        "Lei Complementar",
        "224",
        "2025-12-26",
        "Presidência da República",
        "federal/leis-complementares",
        "Lei Complementar nº 224, de 26 de dezembro de 2025",
        "",
        "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm",
        "planalto-html",
    ),
    Norma(
        "in-rfb-1585-2015",
        "Instrução Normativa RFB",
        "1.585",
        "2015-08-31",
        "Secretaria da Receita Federal do Brasil",
        "rfb/instrucoes-normativas",
        "Instrução Normativa RFB nº 1.585, de 31 de agosto de 2015",
        "Dispõe sobre o imposto sobre a renda incidente sobre os rendimentos e ganhos "
        "líquidos auferidos nos mercados financeiro e de capitais.",
        "https://normasinternet2.receita.fazenda.gov.br/api/consulta-externa/ato/67494/visao/vigente",
        "rfb-api",
    ),
)

_HEADING = re.compile(r"^(CAPÍTULO|Capítulo|SEÇÃO|Seção|Subseção|TÍTULO|Título|LIVRO)\b")
_ARTICLE = re.compile(r"^(Art\.\s*\d+[º°o]?(?:-[A-Z])?\.?|§\s*\d+[º°o]?\.?|Parágrafo único\.?)")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        data: bytes = response.read()
    return data


class _PlanaltoParser(HTMLParser):
    """Collect paragraph texts, skipping <strike> (revoked wording) and scripts."""

    _BLOCKS = frozenset({"p", "div", "h1", "h2", "h3", "h4", "li", "tr", "br"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self._buffer: list[str] = []
        self._strike = 0
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"strike", "s", "del"}:
            self._strike += 1
        elif tag in {"script", "style", "head"}:
            self._skip += 1
        elif tag in self._BLOCKS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"strike", "s", "del"}:
            self._strike = max(0, self._strike - 1)
        elif tag in {"script", "style", "head"}:
            self._skip = max(0, self._skip - 1)
        elif tag in self._BLOCKS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._strike and not self._skip:
            self._buffer.append(data)

    def _flush(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self._buffer)).strip()
        self._buffer = []
        if text:
            self.paragraphs.append(text)

    def close(self) -> None:
        super().close()
        self._flush()


def _decode(raw: bytes) -> str:
    match = re.search(rb"charset=[\"']?([\w-]+)", raw[:4000])
    encoding = match.group(1).decode() if match else "utf-8"
    try:
        return raw.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        return raw.decode("latin-1")


_C1_TO_CP1252 = {
    code: bytes([code]).decode("cp1252", errors="ignore") or " " for code in range(0x80, 0xA0)
}


def planalto_paragraphs(raw: bytes) -> list[str]:
    parser = _PlanaltoParser()
    # Some Planalto pages embed cp1252 punctuation (curly quotes, dashes) as C1 controls.
    parser.feed(_decode(raw).translate(_C1_TO_CP1252))
    parser.close()
    paragraphs = parser.paragraphs
    # Drop the Planalto page header before the norm's own title.
    for index, text in enumerate(paragraphs):
        if re.match(r"^(LEI|Lei)( COMPLEMENTAR)?\s+N[ºo°]", text):
            return paragraphs[index:]
    return paragraphs


def rfb_paragraphs(raw: bytes) -> list[str]:
    payload = json.loads(raw.decode("utf-8"))
    segments = sorted(payload["outrosSegmentos"], key=lambda s: s["ordemSegmentoAto"])
    paragraphs: list[str] = []
    for segment in segments:
        if segment.get("tachado") or segment.get("omitir"):
            continue
        text = html.unescape(re.sub(r"<[^>]+>", "", segment.get("textoIntegra") or ""))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def to_markdown_body(titulo: str, paragraphs: list[str]) -> str:
    lines = [f"# {titulo}", ""]
    for text in paragraphs:
        if _HEADING.match(text):
            lines.append(f"### {text}")
        else:
            lines.append(_ARTICLE.sub(lambda m: f"**{m.group(1)}**", text, count=1))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _yaml(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def front_matter(norma: Norma, sha256: str, baixado_em: str) -> str:
    fields = {
        "schema_versao": SCHEMA_VERSION,
        "id": norma.id,
        "classe": "norma",
        "tipo": norma.tipo,
        "titulo": norma.titulo,
        "orgao": norma.orgao,
        "numero": norma.numero,
        "data": norma.data,
        "versao_texto": (
            "texto compilado da fonte; trechos tachados omitidos, mas redações superadas "
            "sem tachado podem permanecer: confira a anotação '(Redação dada por ...)'"
        ),
        "ementa": norma.ementa,
        "fonte": norma.fonte,
        "sha256_fonte": sha256,
        "formato_fonte": norma.formato,
        "baixado_em": baixado_em,
    }
    body = "\n".join(f"{key}: {_yaml(value)}" for key, value in fields.items())
    return f"---\n{body}\n---\n"


_EMENTA = re.compile(r"^(Dispõe|Altera|Institui|Estabelece|Regulamenta|Disciplina)\s")
_NOTE = re.compile(r"\s*\((Redação dada|Incluído|Vide)[^)]*\)\s*$")


def official_ementa(paragraphs: list[str], fallback: str) -> str:
    """The ementa as published (first paragraph that reads like one), else ``fallback``."""
    for text in paragraphs[:15]:
        if _EMENTA.match(text):
            return _NOTE.sub("", text).strip()
    return fallback


def publish(norma: Norma, raw: bytes, out_dir: Path, today: str) -> Path:
    paragraphs = rfb_paragraphs(raw) if norma.formato == "rfb-api" else planalto_paragraphs(raw)
    if norma.formato == "planalto-html":
        norma = replace(norma, ementa=official_ementa(paragraphs, norma.ementa))
    sha256 = hashlib.sha256(raw).hexdigest()
    target = out_dir / norma.pasta / norma.data[:4] / f"{norma.id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    content = front_matter(norma, sha256, today) + to_markdown_body(norma.titulo, paragraphs)
    target.write_text(content, encoding="utf-8", newline="\n")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--saida", default="legislacao", type=Path)
    args = parser.parse_args()
    today = date.today().isoformat()  # noqa: DTZ011 - download date is local by design
    for norma in NORMAS:
        path = publish(norma, fetch(norma.fonte), args.saida, today)
        print(f"{norma.id}: {path}")


if __name__ == "__main__":
    main()
