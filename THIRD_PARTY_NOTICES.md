# Avisos de terceiros

## Dados

- **`src/b3_ir/data/ativos.csv`**: derivado das Séries Históricas de cotações
  (COTAHIST) publicadas pela B3 S.A. – Brasil, Bolsa, Balcão em
  <https://www.b3.com.br/>. Contém apenas ticker, classe, nome de pregão,
  especificação e a data da última cotação vista. O b3-ir não tem vínculo com a B3.
- **`legislacao/`**: textos de leis e atos oficiais (Planalto e Receita Federal),
  não protegidos por direito autoral (Lei 9.610/1998, art. 8º, IV).

## Dependências opcionais

- **correpy** (Apache-2.0), usado só com o extra `pdf` para ler notas SINACOR.
  Depende do **PyMuPDF**, licenciado como **AGPL-3.0** (ou licença comercial da
  Artifex). Quem instala `b3-ir[pdf]` deve observar os termos da AGPL-3.0.
