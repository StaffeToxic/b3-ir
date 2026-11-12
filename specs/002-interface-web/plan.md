# Plan: local web interface

**Spec**: [spec.md](spec.md)

## Technical Context

- Python stdlib only: `http.server.ThreadingHTTPServer`, `json`, `tempfile`, `secrets`,
  `webbrowser`. No Flask/FastAPI (Constitution VII).
- Front end: one static `index.html` (vanilla JS, inline CSS) in package data
  `b3_ir/web/static/`. Files are sent as base64 JSON with their relative path.
- Shared input loading moves from `cli.py` to `b3_ir/inputs.py`, used by CLI and web.

## Contract

- `GET /?t=<token>` → the page.
- `POST /api/analisar` (header `X-B3IR-Token`) body
  `{"arquivos": [{"caminho": "xp/nota.pdf", "base64": "..."}]}` →
  `{"anos": [...], "posicoes": [...], "mensal": {"2026": [...]}, "anual": {"2026": {...}},
  "avisos": [...], "nao_suportados": [...], "ignorados": [...]}`; 400 on bad request,
  403 without token, 413 above 50 MB, 422 when the data cannot be computed (message).

## Visual direction (inspired by themaestri.app, no assets copied)

Geist/system sans, near-black text, lavender hero gradient with dot grid, floating
translucent pill bar, dark pill buttons, results inside a window frame with a
sidebar, light vs dark summary cards.

## Constitution Check

IV is amended (PATCH): a loopback-only local UI is allowed; still no outbound
requests. Architecture test restricts `http.server` to `b3_ir/web`.
