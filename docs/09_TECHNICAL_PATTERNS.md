# 09. Technical Patterns & UX Rules

Este arquivo documenta as diretrizes técnicas absolutas descobertas durante a evolução do Nexo. A Inteligência Artificial deve checar essas regras para evitar a reintrodução de bugs estruturais (regressão).

## 1. Banco de Dados e SQLite (Persistência)
Sempre que realizar operações de modificação no banco de dados (`INSERT`, `UPDATE` ou cláusulas `ON CONFLICT`) utilizando o SQLite em Python, é **obrigatório** chamar o comando `c.commit()` explicitamente antes de fechar a conexão.
- **Motivo:** O ambiente atual descarta operações executadas apenas em memória na hora em que o aplicativo é reiniciado, causando perda silenciosa de configurações.

## 2. IA e APIs Externas (Modo Resiliência)
Nunca dependa de uma única versão fixa de modelo da IA (ex: `gemini-1.5-flash`). Modelos fixos são frequentemente descontinuados e servidores gratuitos sofrem gargalos severos de processamento (Erro 503), principalmente em tarefas pesadas como Visão Computacional.
- **Padrão:** Utilize sempre apelidos auto-atualizáveis (`gemini-flash-latest`, `gemini-flash-lite-latest`) e implemente uma lógica de **fallback em cascata** com múltiplas tentativas. Se um modelo pesado falhar, o código deve silenciosamente tentar um modelo mais leve antes de devolver o erro à interface.

## 3. Comportamento de Janelas e Menus Tkinter (Fim dos Fantasmas)
O uso indiscriminado da propriedade `attributes('-topmost', True)` deve ser evitado a todo custo, pois força as janelas do Nexo a ficarem sobrepostas a outros aplicativos do Sistema Operacional (ex: navegadores).
- **Janelas Secundárias Comuns:** Para telas de visualização e formulários com barra de título normal, utilize sempre `transient(parent)`. Isso garante que a janela minimize junto com o Nexo e obedeça ao foco do Windows.
- **Menus Personalizados (overrideredirect):** Janelas que removem as bordas nativas exigem o uso do `-topmost` no Windows para funcionarem e não afundarem. No entanto, é **obrigatório** implementar um evento de destruição (`destroy()`) da janela atrelado a cliques externos. 
  - **A Armadilha do Foco (Tkinter Focus Trap):** NUNCA vincule o evento `<FocusOut>` à Janela Principal (`root.bind('<FocusOut>')`) para tentar fechar menus. Qualquer clique em um botão interno troca o foco e faz a Janela Principal disparar o evento instantaneamente, destruindo o menu antes mesmo dele aparecer. O evento de `<FocusOut>` só pode ser atrelado ao próprio menu, ou deve-se usar um rastreador de cliques (`<Button-1>`) fora das coordenadas do menu.

## 4. Filtros de Entrada em Arquivos (Prevenção > Tratamento)
A validação de formatos suportados pelo sistema não deve ocorrer apenas "depois" do carregamento para tentar tratar o erro no Python. 
- **Padrão:** Sempre que o sistema solicitar o anexo de um arquivo (via `filedialog.askopenfilename`), o parâmetro `filetypes` deve restringir as opções *estritamente* aos formatos suportados por aquela função (ex: permitir apenas Imagens e PDFs para o importador da receita). Isso oculta arquivos indesejados da visão do usuário e previne quebra de sistema.
