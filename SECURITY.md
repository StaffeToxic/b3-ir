# Política de segurança

## Versões com suporte

Só a versão mais recente recebe correções de segurança.

## Como relatar uma vulnerabilidade

**Não abra issue pública.** Use o relato privado do GitHub:
[Security → Report a vulnerability](https://github.com/StaffeToxic/b3-ir/security/advisories/new).

Inclua o que for possível: versão, sistema operacional, passos para reproduzir e o
impacto. **Nunca anexe notas de corretagem, extratos ou dados pessoais reais**; use
valores fictícios.

Prazo de resposta esperado: confirmação em até 7 dias e, se a falha for confirmada,
uma correção ou orientação em até 30 dias.

## Escopo

Interessam especialmente:

- a interface local (`b3-ir web`): acesso de outro computador, contorno do token,
  leitura de arquivos fora da pasta temporária, execução de código pela página;
- a leitura de arquivos (PDF, XLSX, CSV) que permita executar código ou ler/escrever
  fora do esperado;
- qualquer envio de dados para a internet, que o projeto proíbe.

Erros de cálculo de imposto não são vulnerabilidades: abra uma issue normal, com
valores fictícios e a conta feita à mão.

## Verificar os arquivos da release

Desde a v0.1.1, os executáveis e pacotes vêm com atestado de origem: prova de que
foram gerados pelo CI deste repositório a partir de um commit público. Com o
[GitHub CLI](https://cli.github.com/):

```bash
gh attestation verify b3-ir-windows-x64.exe --repo StaffeToxic/b3-ir
```

Cada release também publica o `SHA256SUMS.txt`.
