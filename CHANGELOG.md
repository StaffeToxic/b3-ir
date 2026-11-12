# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- Especificação, plano e contratos do MVP (`specs/001-ir-mvp/`).
- Termo de isenção de responsabilidade.
- Estrutura do pacote, CI, modelos de domínio e registro de regras fiscais.
- Núcleo de cálculo: preço médio, day trade, apuração mensal, DARF.
- CLI `mensal` e `posicoes` com entrada em CSV.
- Textos oficiais das leis e da IN RFB 1.585/2015 em `legislacao/`, com regras
  verificadas e rastreáveis.

- Leitura de notas SINACOR em PDF via correpy (extra opcional `pdf`).
- Catálogo de ativos do COTAHIST da B3: resolve o nome de pregão da nota para o
  ticker e classifica FII, ETF e ação.

- Extratos da Área do Investidor da B3 (Negociação e Movimentação) e deduplicação
  entre notas e extrato.

- Relatório anual (`b3-ir anual`): bens e direitos em 31/12, renda variável mês a
  mês, rendimentos isentos e JCP, em texto, JSON e CSV para Excel.
- Regras com vigência: IRRF sobre JCP de 15% até 2025 e 17,5% a partir de 2026 (LC
  224/2025); retenção sobre dividendos acima de R$ 50 mil/mês a partir de 2026.
- Leis 9.249/1995 e 9.250/1995 e LC 224/2025 em `legislacao/`.

### Corrigido
- Day trade agora exige a mesma corretora (Lei 9.959/2000, art. 8º).
- Saldo de IRRF não passa de um ano para o outro.
