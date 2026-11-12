# Feature Specification: local web interface

**Feature Branch**: `002-interface-web` | **Created**: 2026-11-12 | **Status**: Draft

**Input**: "Uma interface de fácil uso, inspirada no site do Maestri."

## User Scenarios

### US1 — Drop files, see the result (P1)

The investor runs `b3-ir web`; the browser opens a local page. They drag notes (PDF),
B3 statements (XLSX) or the manual CSV — or a whole folder, one subfolder per broker —
and see, without touching the terminal: monthly assessment with DARF, current
positions, and the annual return data, plus every warning and refused item.

**Acceptance**: dropping `examples/operacoes.csv` shows the May DARF of R$ 91,81 due
30/06/2026, ITSA4 in the positions, and the 2026 annual data; a refused file is
listed with its reason; the disclaimer is always visible.

### US2 — Take the data out (P2)

From the annual view the investor downloads the "Bens e Direitos" table as CSV
(Excel pt-BR) and the full result as JSON.

## Requirements

- **FR-W01**: `b3-ir web [--porta N] [--nao-abrir]` serves the UI on 127.0.0.1 only.
- **FR-W02**: Files are processed by the same code as the CLI; results identical.
- **FR-W03**: Uploaded files live only in a temporary folder deleted after each
  analysis; nothing is persisted, no outbound request is made (no CDN, no fonts).
- **FR-W04**: Every API request must carry the per-session token printed in the URL.
- **FR-W05**: Folder structure of a dropped folder is kept, so the PDF's parent
  folder still names the broker (research D-R4-1). File names are sanitized.
- **FR-W06**: Disclaimer visible on every screen (Constitution VI).

## Success Criteria

- **SC-W01**: From `b3-ir web` to the monthly result in under 30 s for a year of notes.
- **SC-W02**: API results equal the CLI JSON for the example year (tested).
- **SC-W03**: The server refuses non-loopback binding and requests without token (tested).
