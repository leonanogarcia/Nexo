# 08. Roadmap de Produção (Instalador .exe)

Este documento registra as obrigações arquiteturais que devem ser cumpridas ANTES de compilar o software final para distribuição no Windows (ex: via PyInstaller).

## 1. Migração do Sistema de Arquivos (AppData)
- **Status Atual (Dev):** O sistema está configurado em modo "Portátil". Os arquivos de configuração (ex: `nexo_config.json`) e o banco de dados (`nexo.db`) são salvos e lidos no diretório raiz (`BASE_DIR`) onde o `main.py` é executado.
- **Ação Obrigatória para Produção:** Quando o software for compilado para rodar em `C:\Arquivos de Programas`, o Windows bloqueará a gravação de arquivos por questões de segurança. O endereço de salvamento das memórias do sistema (configurações, preferências de tabela, visibilidade de colunas) **deve** ser alterado para o diretório seguro do usuário: `os.environ.get('APPDATA') + '/Nexo'`.

## 2. Empacotamento de Assets
- Os caminhos de imagens e fontes devem usar `sys._MEIPASS` em tempo de execução quando compilados pelo PyInstaller, caso contrário os assets visuais quebrarão na máquina do cliente.


## 3. Regras Obrigatórias Antes de Gerar Executável / Instalador (.exe / Setup)
> **REGRA INQUEBRÁVEL:** Antes de compilar qualquer executável ou instalador do Nexo 2.0, a IA **É OBRIGADA** a ler este arquivo e conferir todos os itens abaixo:

1. **Banco de Dados 100% Zerado (Proibido Dados de Teste):**
   - **Jamais** incluir `nexo.db`, `nexo_config.json`, `backups/` ou `documentos/` pessoais/de desenvolvimento dentro do `.exe` ou do instalador Inno Setup.
   - Na primeira execução no computador do cliente, o `init_db()` deve criar um `nexo.db` limpo do zero dentro de `%LOCALAPPDATA%\Nexo`.
2. **Botão `🔄 Recarregar` Oculto em Produção:**
   - O botão `🔄 Recarregar` do cabeçalho (`App.tsx`) é ferramenta exclusiva de desenvolvimento (`!status.is_packaged`).
   - Quando empacotado (`getattr(sys, "frozen", False)`), `/api/status` retorna `is_packaged: True` e o botão deve ficar **oculto automaticamente** na interface.
3. **Entrypoint e Build Atualizados:**
   - O empacotamento da v2.0 deve usar **`main.py`**, garantindo que `frontend/dist` (gerado por `npm --prefix frontend run build`) esteja atualizado e incluído no bundle junto com `ui_assets/`, `nexo_icon.ico`, `nexo_icon.png`, `nexo_logo.png` e `backend/`.
