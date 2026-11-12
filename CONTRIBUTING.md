# Contribuindo com o b3-ir

Obrigado pelo interesse! Antes de abrir um PR:

1. Leia a [constituição do projeto](.specify/memory/constitution.md). Quatro
   princípios são inegociáveis: regra fiscal com fonte legal citada, dinheiro em
   `Decimal`, testes com casos calculados à mão e privacidade.
2. Abra uma issue descrevendo o problema ou a regra. **Nunca anexe notas de
   corretagem, extratos ou dados pessoais reais.** Use valores fictícios.
3. Para regras fiscais novas ou alteradas, inclua a fonte oficial (lei, instrução
   normativa, artigo) e atualize `docs/regras-fiscais.md` e `src/b3_ir/rules.py`.

## Ambiente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest && ruff check . && ruff format --check . && mypy
```

## Convenções

- Código, identificadores, comentários e commits em inglês; documentação de
  usuário e mensagens da CLI em português.
- [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`...).
- Um PR por mudança lógica, com testes.
