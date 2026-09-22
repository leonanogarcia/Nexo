# Nexo — Gestão de Custos e Precificação

Versão 0.7.4 — correções visuais pontuais sobre a base 0.7.1/0.7.2.

## Interface atual
- Início: indicadores, BI mensal de compras por item e por marca e evolução de custos de Receitas Base e Produtos.
- Cadastro: fonte central de Insumos, com categoria Comestível/Não comestível, histórico de compras e conversões configuráveis por insumo.
- Receita: lista com janelas de criação/edição, busca somente no Cadastro, custo automático, histórico e importação/exportação de documentos.
- Produtos: lista com janelas de criação/edição e composição usando Insumos, Receita ou outros Produtos.
- Configurações: tema, identidade da empresa, custos operacionais, unidades internas mínimas, conversões por insumo e caminho do SQLite. O desenvolvimento de novas funções em Configurações permanece fora desta rodada.

## Códigos
- Insumo: `INS_0001`
- Receita: `RB_0001`
- Produto: `PROD_0001`

Os códigos são sequenciais por tipo e não devem ser reutilizados.

## Execução para desenvolvimento
Use `run_nexo.bat` ou:

```cmd
python main.py
```

Não é necessário gerar EXE a cada alteração.

## Documento Word/PDF
O núcleo funciona sem bibliotecas externas. Os recursos de leitura/exportação de Word e PDF usam bibliotecas opcionais:
- `python-docx`
- `pypdf`
- `reportlab`

Instale-as somente quando for testar esses recursos.

## Banco
SQLite local é o padrão. O caminho do arquivo pode ser alterado em Configurações. A estrutura de acesso ao banco fica centralizada para permitir conectores de servidor em uma etapa futura, sem misturar isso com a interface.
