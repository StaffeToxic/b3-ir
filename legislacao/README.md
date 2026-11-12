# Legislação

Textos oficiais das normas que fundamentam as regras do b3-ir, em Markdown
versionado. O formato segue o do projeto
[normas-cvm](https://github.com/StaffeToxic/normas-cvm): um arquivo por norma em
`<órgão>/<família>/<ano>/<id>.md`, com metadados em YAML.

| Norma | Arquivo | Usada para |
|---|---|---|
| Lei 8.668/1993 | [federal/leis/1993/lei-8668-1993.md](federal/leis/1993/lei-8668-1993.md) | Alíquota de FII |
| Lei 8.981/1995 | [federal/leis/1995/lei-8981-1995.md](federal/leis/1995/lei-8981-1995.md) | Custo médio, compensação de perdas |
| Lei 9.249/1995 | [federal/leis/1995/lei-9249-1995.md](federal/leis/1995/lei-9249-1995.md) | Dividendos isentos (art. 10); IRRF sobre JCP (art. 9º, § 2º) |
| Lei 9.250/1995 | [federal/leis/1995/lei-9250-1995.md](federal/leis/1995/lei-9250-1995.md) | Retenção sobre dividendos acima de R$ 50 mil/mês a partir de 2026 (art. 6º-A) |
| Lei 9.430/1996 | [federal/leis/1996/lei-9430-1996.md](federal/leis/1996/lei-9430-1996.md) | DARF mínimo de R$ 10 |
| Lei 9.779/1999 | [federal/leis/1999/lei-9779-1999.md](federal/leis/1999/lei-9779-1999.md) | Redação atual do art. 18 da Lei 8.668 (FII) |
| Lei 9.959/2000 | [federal/leis/2000/lei-9959-2000.md](federal/leis/2000/lei-9959-2000.md) | Day trade: definição e IRRF de 1% |
| Lei 11.033/2004 | [federal/leis/2004/lei-11033-2004.md](federal/leis/2004/lei-11033-2004.md) | Alíquotas, IRRF de 0,005%, isenção de R$ 20 mil |
| Lei 15.270/2025 | [federal/leis/2025/lei-15270-2025.md](federal/leis/2025/lei-15270-2025.md) | Retenção sobre dividendos a partir de 2026 |
| LC 224/2025 | [federal/leis-complementares/2025/lcp-224-2025.md](federal/leis-complementares/2025/lcp-224-2025.md) | IRRF sobre JCP de 17,5% a partir de 2026 (arts. 8º e 14, III) |
| IN RFB 1.585/2015 | [rfb/instrucoes-normativas/2015/in-rfb-1585-2015.md](rfb/instrucoes-normativas/2015/in-rfb-1585-2015.md) | Regulamentação da renda variável |

## Metadados

| Campo | Significado |
|---|---|
| `id` | Identificador estável (`lei-11033-2004`) |
| `tipo`, `numero`, `data`, `orgao`, `titulo` | Identificação da norma |
| `ementa` | Ementa como publicada no texto oficial |
| `versao_texto` | Texto compilado da fonte na data do download. Trechos tachados são omitidos, mas o Planalto nem sempre tacha redações antigas: quando um dispositivo aparece mais de uma vez, vale o de anotação mais recente |
| `fonte` | URL oficial baixada |
| `sha256_fonte` | SHA-256 dos bytes baixados, para conferir a origem |
| `formato_fonte` | `planalto-html` ou `rfb-api` |
| `baixado_em` | Data do download |

## Atualizar

```bash
python scripts/atualizar_legislacao.py
```

O script baixa as fontes, regenera os arquivos e atualiza o SHA-256. Revise o
`git diff`: uma mudança no texto de uma norma pode exigir atualizar
[`src/b3_ir/rules.py`](../src/b3_ir/rules.py) e
[`docs/regras-fiscais.md`](../docs/regras-fiscais.md).

## Aviso

Esta é uma cópia para consulta e rastreabilidade. Os textos de lei e atos
oficiais não são protegidos por direito autoral (Lei 9.610/1998, art. 8º, IV).
**Somente os textos publicados no Diário Oficial da União têm valor legal.**
