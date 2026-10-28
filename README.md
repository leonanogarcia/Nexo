# Nexo — Gestão de Custos, Ficha Técnica e Precificação

**Versão 1.0.0** — Sistema desktop para Windows voltado ao controle de insumos, fichas técnicas de receitas em cascata, precificação de produtos e análise gerencial (BI) de compras e evolução de custos.

---

## Principais Recursos (v1.0.0)

- **Início & BI Gerencial:**
  - Painéis de resumo rápido para **Produtos**, **Receitas Base** e **Insumos** cadastrados.
  - Gráficos visuais de rosca (*Donut Charts*) para **Distribuição de Compras por Insumo** e **Composição de Custos (Receitas e Produtos)**.
  - **Modal dedicado de BI:** Tabelas comparativas detalhadas com filtro de busca, seleção de período mensal e ordenação por coluna (*Por Insumo*, *Por Marca* e *Evolução de Receitas e Produtos*).
- **Cadastro de Insumos (`INS_0001`):**
  - Fonte central de matérias-primas e itens de acabamento (*Comestível* / *Não comestível*).
  - Histórico completo de compras com atualização automática de custo e registro de marcas/fornecedores.
  - Conversões e equivalências customizadas por insumo (ex.: xícara, colher, pacote → gramas ou mililitros).
- **Receitas Base (`RB_0001`):**
  - Composição de fichas técnicas vinculadas ao Cadastro de Insumos, com cálculo automático de custo total e rendimento.
  - Suporte a anexos, importação assistida e exportação de fichas técnicas em Word (`.docx`) e PDF.
- **Produtos (`PROD_0001`):**
  - Montagem de produtos finais combinando **Insumos**, **Receitas Base** ou outros **Produtos**.
  - Cálculo automático de **Custo Direto**, **Custos Operacionais Indiretos** (Gás, Energia, Água), **Preço de Venda** e **Margem de Lucro**.
- **Configurações & Auditoria:**
  - Alternância entre **Modo Claro** e **Modo Escuro** com o Design System Nexo em formato cápsula.
  - Parâmetros de identidade da empresa, taxas de custos operacionais, unidades internas mínimas (`mg`, `ml`, `un`) e retenção de histórico.
  - Auditoria integrada do banco de dados com registro de alterações (`INSERT`, `UPDATE`, `DELETE`) e justificativas de edição.

---

## Arquitetura do Projeto

O Nexo v1.0.0 é dividido em camadas independentes (`backend/` e `frontend/`), permitindo manutenção limpa e futura expansão para API/Mobile:

```text
Nexo/
├── backend/                     # Núcleo e regras de negócio (independente de interface gráfica)
│   ├── paths.py                 # Resolução de diretórios Windows (%LOCALAPPDATA%\Nexo) e backups
│   ├── database.py              # Conexão SQLite, migrações, códigos sequenciais e triggers de auditoria
│   ├── units.py                 # Motor de conversão de medidas e equivalências por insumo
│   ├── calculator.py            # Fórmulas de custo de insumos, receitas em cascata, rateio e margem
│   └── document_importer.py     # Importação/leitura de documentos Word e PDF
│
├── frontend/                    # Interface gráfica no Padrão Visual Nexo (Capsule Design System)
│   ├── components.py            # Componentes reutilizáveis (RoundedPanel, RoundedEntry, RoundedDropdown, etc.)
│   ├── app.py                   # Janela principal, barra lateral (ReferenceSidebar) e gerenciamento de temas
│   └── pages/                   # Módulos separados por aba
│       ├── home_page.py         # Aba Início, gráficos de rosca e Modal de BI
│       ├── materials_page.py    # Aba Cadastro de Insumos
│       ├── recipes_page.py      # Aba Receitas Base
│       ├── products_page.py     # Aba Produtos
│       ├── settings_page.py     # Aba Configurações e Auditoria
│       └── table_helpers.py     # Utilitários de tabelas customizadas e ações em lote
│
├── installer/                   # Scripts de empacotamento para Windows (.exe e Inno Setup)
│   ├── gerar_executavel.bat     # Gera o executável Nexo.exe via PyInstaller
│   └── nexo_setup.iss           # Script para geração do instalador Windows (Instalador_Nexo_v1.0.0.exe)
│
├── docs/                        # Especificações técnicas e diretrizes do Design System Nexo
└── main.py                      # Ponto de entrada da aplicação
```

---

## Banco de Dados e Execução Sem Acesso Administrador

- **Armazenamento inteligente no Windows:** Quando executado a partir de uma instalação padrão (ex.: `C:\Arquivos de Programas\Nexo`), o Nexo grava automaticamente o banco SQLite (`nexo.db`), as configurações (`nexo_config.json`), os documentos anexados e os backups diários em **`%LOCALAPPDATA%\Nexo`** (`C:\Users\<Usuario>\AppData\Local\Nexo`).
- Isso garante que **qualquer usuário do Windows consiga utilizar o Nexo normalmente mesmo sem privilégios de Administrador**, preservando os dados em atualizações de versão.
- O caminho do arquivo SQLite também pode ser personalizado a qualquer momento na aba **Configurações > Banco de Dados & BI**.

---

## Como Executar (Modo Desenvolvimento)

Utilize o atalho `run_nexo.bat` ou execute diretamente via terminal:

```cmd
python main.py
```

### Dependências Opcionais (Word / PDF)
Para utilizar os recursos de leitura e exportação de arquivos Word e PDF, instale as bibliotecas opcionais (ou execute `instalar_documentos.bat`):
- `python-docx`
- `pypdf`
- `reportlab`

---

## Como Gerar o Executável / Instalador Windows

1. Execute `installer\gerar_executavel.bat` para empacotar o aplicativo em `dist\Nexo\Nexo.exe`.
2. Para gerar o instalador único (`Instalador_Nexo_v1.0.0.exe`), compile o arquivo `installer\nexo_setup.iss` utilizando o **Inno Setup**.
