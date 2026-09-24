# Memória de Contexto da IA (Projeto Nexo)

> **ATENÇÃO IA:** As regras absolutas de negócio, design e arquitetura do sistema agora residem na pasta `docs/`. Você **É OBRIGADO** a consultar e respeitar os arquivos dentro de `docs/` antes de tomar qualquer ação no código.

## Documentação Oficial (Single Source of Truth)
- `docs/01_CORE_DIRECTIVES.md`: Protocolos da IA, proibição de usar componentes feios para coisas novas. Regra "Qualidade > Velocidade".
- `docs/02_DESIGN_SYSTEM.md`: Biblioteca de componentes (Cápsulas, Cores, Hitboxes, Toplevels). OBRIGATÓRIO para novas telas.
- `docs/03_DATABASE_SCHEMA.md`: Estrutura do BD, auto-migrações e integridade referencial.
- `docs/04_MODULE_MATERIALS.md`: Regras do módulo de Insumos (Cadastro).
- `docs/05_MODULE_RECIPES_PRODUCTS.md`: Regras de Receitas e Produtos, incluindo a lei inquebrável de dependência funcional (puxar insumos sem falhar).
- `docs/06_MODULE_SETTINGS_SIDEBAR.md`: Layout da Sidebar, estado de foco, responsividade, e configurações do sistema.

## Status Atual
- Em processo de refatoração para aplicar o Design System universalmente. Existem divergências no código atualmente (componentes antigos), mas o que dita a regra ideal é a pasta `docs/`.
- Regra de Conduta: **LEIA -> REPENSE -> PROPONHA -> SÓ ENTÃO EXECUTE (se aprovado)**.
