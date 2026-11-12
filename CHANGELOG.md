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

### Corrigido
- Day trade agora exige a mesma corretora (Lei 9.959/2000, art. 8º).
- Saldo de IRRF não passa de um ano para o outro.
