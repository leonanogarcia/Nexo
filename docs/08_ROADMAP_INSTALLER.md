# 08. Roadmap de Produção (Instalador .exe)

Este documento registra as obrigações arquiteturais que devem ser cumpridas ANTES de compilar o software final para distribuição no Windows (ex: via PyInstaller).

## 1. Migração do Sistema de Arquivos (AppData)
- **Status Atual (Dev):** O sistema está configurado em modo "Portátil". Os arquivos de configuração (ex: `nexo_config.json`) e o banco de dados (`nexo.db`) são salvos e lidos no diretório raiz (`BASE_DIR`) onde o `main.py` é executado.
- **Ação Obrigatória para Produção:** Quando o software for compilado para rodar em `C:\Arquivos de Programas`, o Windows bloqueará a gravação de arquivos por questões de segurança. O endereço de salvamento das memórias do sistema (configurações, preferências de tabela, visibilidade de colunas) **deve** ser alterado para o diretório seguro do usuário: `os.environ.get('APPDATA') + '/Nexo'`.

## 2. Empacotamento de Assets
- Os caminhos de imagens e fontes devem usar `sys._MEIPASS` em tempo de execução quando compilados pelo PyInstaller, caso contrário os assets visuais quebrarão na máquina do cliente.
