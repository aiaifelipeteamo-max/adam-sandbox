"""Adam desktop agent: server-side reasoning loop; the local PC program executes each action with user permission."""
import json
import time
import uuid

from emergentintegrations.llm.chat import ImageContent, LlmChat, StreamDone, TextDelta, ToolCallReady, UserMessage

SESSIONS: dict = {}
MAX_STEPS = 60
TTL = 10800

SYSTEM = """Você é Adam, agente de computador criado por Felipe Hudson (Belo Horizonte, Brasil). Você controla o computador do usuário (mouse, teclado, programas e navegador), com a permissão dele, para cumprir tarefas.
A cada passo você recebe uma captura de tela. As coordenadas (x, y) que você usar são em pixels DA CAPTURA recebida (canto superior esquerdo = 0,0).
Regras:
- Use UMA ferramenta por vez. Depois de cada ação você recebe uma nova captura: confira o resultado antes de seguir.
- Prefira atalhos de teclado e abrir programas/URLs diretamente quando for mais confiável que clicar.
- Para pesquisar na web, use abrir com https://www.google.com/search?q=termos
- Nunca digite senhas, dados de cartão, nem finalize compras, pagamentos, envios sensíveis ou exclusões sem que a tarefa peça isso explicitamente.
- Use executar_comando só quando necessário, com comandos simples e seguros; explique o motivo no campo motivo.
- Se uma ação for negada pelo usuário, não insista: siga outro caminho ou explique.
- Quando terminar (ou se não for possível), responda SEM chamar ferramentas, com um resumo claro em português."""

_motivo = {"motivo": {"type": "string", "description": "Por que esta ação (mostrado ao usuário ao pedir permissão)."}}


def _tool(name, desc, props, req):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": {**props, **_motivo}, "required": req}}}


DESKTOP_TOOLS = [
    _tool("clicar", "Clica na posição (x, y) da captura.", {"x": {"type": "integer"}, "y": {"type": "integer"},
          "botao": {"type": "string", "enum": ["esquerdo", "direito"]}, "duplo": {"type": "boolean"}}, ["x", "y"]),
    _tool("digitar", "Digita texto onde o cursor estiver.", {"texto": {"type": "string"}}, ["texto"]),
    _tool("tecla", "Pressiona tecla ou atalho, ex.: enter, esc, tab, ctrl+l, alt+tab, win+r.", {"teclas": {"type": "string"}}, ["teclas"]),
    _tool("rolar", "Rola a tela na posição atual do mouse.", {"direcao": {"type": "string", "enum": ["baixo", "cima"]},
          "quantidade": {"type": "integer", "description": "1 a 20"}}, ["direcao"]),
    _tool("mover_mouse", "Move o mouse até (x, y) sem clicar.", {"x": {"type": "integer"}, "y": {"type": "integer"}}, ["x", "y"]),
    _tool("abrir", "Abre uma URL no navegador padrão, um arquivo/pasta ou um programa (ex.: notepad, calc, chrome).",
          {"alvo": {"type": "string"}}, ["alvo"]),
    _tool("executar_comando", "Executa um comando no terminal do sistema (PowerShell no Windows) e devolve a saída.",
          {"comando": {"type": "string"}}, ["comando"]),
    _tool("ver_tela", "Tira uma nova captura de tela.", {}, []),
    _tool("aguardar", "Espera alguns segundos.", {"segundos": {"type": "integer", "description": "1 a 30"}}, ["segundos"]),
]


def _screen_msg(text: str, shot: dict) -> UserMessage:
    info = f"{text}\nCaptura: {shot.get('width')}x{shot.get('height')} px. Sistema: {shot.get('os', '?')}."
    if shot.get("image"):
        return UserMessage(text=info, file_contents=[ImageContent(shot["image"])])
    return UserMessage(text=info + "\n(sem captura de tela)")


def _gc():
    limit = time.time() - TTL
    for sid in [k for k, s in SESSIONS.items() if s["created"] < limit]:
        SESSIONS.pop(sid, None)


async def _advance(s: dict, msg) -> str:
    text = []
    async for ev in s["chat"].stream_message(msg):
        if isinstance(ev, TextDelta):
            text.append(ev.content)
        elif isinstance(ev, ToolCallReady):
            s["pending"].append(ev.tool_call)
        elif isinstance(ev, StreamDone):
            break
    return "".join(text).strip()


def _next(s: dict, message: str) -> dict:
    if s["pending"]:
        tc = s["pending"][0]
        args = tc.arguments if isinstance(tc.arguments, dict) else json.loads(tc.arguments or "{}")
        return {"session_id": s["id"], "done": False, "message": message, "step": s["steps"],
                "action": {"id": tc.id, "name": tc.name, "args": args}}
    SESSIONS.pop(s["id"], None)
    return {"session_id": s["id"], "done": True, "message": message or "Tarefa concluída.", "step": s["steps"], "action": None}


async def start(api_key: str, model: tuple, user_id: str, task: str, shot: dict, context: str = "") -> dict:
    _gc()
    sid = str(uuid.uuid4())
    chat = LlmChat(api_key=api_key, session_id=sid, system_message=SYSTEM + context).with_model(*model).with_tools(DESKTOP_TOOLS, tool_choice="auto")
    s = {"id": sid, "user_id": user_id, "chat": chat, "pending": [], "steps": 0, "created": time.time()}
    SESSIONS[sid] = s
    return _next(s, await _advance(s, _screen_msg(f"Tarefa: {task}", shot)))


async def step(sid: str, user_id: str, tool_call_id: str, result: dict) -> dict:
    s = SESSIONS.get(sid)
    if not s or s["user_id"] != user_id:
        raise KeyError("Sessão não encontrada ou expirada")
    if not s["pending"] or s["pending"][0].id != tool_call_id:
        raise KeyError("Ação inesperada")
    tc = s["pending"].pop(0)
    s["steps"] += 1
    if result.get("denied"):
        content = "O usuário NEGOU esta ação. Não repita; siga outro caminho ou explique."
    elif result.get("error"):
        content = f"Erro ao executar: {str(result['error'])[:500]}"
    else:
        content = "Ação executada." + (f"\nSaída:\n{str(result['output'])[:3000]}" if result.get("output") else "")
    s["chat"].add_tool_result(tc.id, content)
    if s["pending"]:
        return _next(s, "")
    if s["steps"] >= MAX_STEPS:
        SESSIONS.pop(sid, None)
        return {"session_id": sid, "done": True, "message": "Limite de passos atingido. Divida a tarefa em partes menores.", "step": s["steps"], "action": None}
    shot = result.get("screen") or {}
    return _next(s, await _advance(s, _screen_msg("Nova captura de tela após a ação.", shot) if shot.get("image") else None))


def stop(sid: str):
    SESSIONS.pop(sid, None)
