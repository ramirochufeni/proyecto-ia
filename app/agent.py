
import os, json, asyncio, httpx
from pathlib import Path
from dotenv import load_dotenv

from app.tools import calc, weather, note_add, note_list, note_delete


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT / ".env")

OPENAI_BASE  = os.getenv("OPENAI_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_KEY   = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = (
    "Sos un asistente en español. Usá herramientas cuando sirvan.\n"
    "Si el usuario pide una operación aritmética, usá SIEMPRE la tool 'calc'.\n"
    "Respondé corto y claro; si falta un dato, pedí 1 aclaración.\n"
)


def build_tool_schemas():
    return [
        {
            "type": "function",
            "function": {
                "name": "calc",
                "description": "Calculadora aritmética segura",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expr": {"type": "string", "description": "expresión, ej 12*(3+4)"}
                    },
                    "required": ["expr"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "clima",
                "description": "Obtener clima de una ciudad (próximas horas, °C)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "ej 'Córdoba, AR'"}
                    },
                    "required": ["city"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "notas_agregar",
                "description": "Agregar una nota de texto",
                "parameters": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "notas_listar",
                "description": "Listar últimas notas",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "notas_borrar",
                "description": "Borrar nota por ID",
                "parameters": {
                    "type": "object",
                    "properties": {"note_id": {"type": "integer"}},
                    "required": ["note_id"],
                },
            },
        },
    ]



def _sanitize(history: list[dict]) -> list[dict]:
    """Filtra/normaliza mensajes del historial para que el LLM no falle."""
    out = []
    for m in history or []:
        role = str(m.get("role", "")).lower()
        content = str(m.get("content", "")).strip()
        if role in {"user", "assistant", "system"} and content:
            out.append({"role": role, "content": content})
    return out

def _extract_message_content(resp: dict) -> str:
    """Saca un texto seguro de la respuesta del LLM, evitando KeyError."""
    try:
        msg = resp["choices"][0].get("message") or {}
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content
        return "(sin contenido del modelo)"
    except Exception as e:
        return f"(no se pudo extraer contenido: {e})"



async def call_llm(messages, tools, max_retries: int = 3):
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    payload = {"model": OPENAI_MODEL, "messages": messages, "tools": tools, "tool_choice": "auto"}

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60, base_url=OPENAI_BASE, headers=headers) as client:
                r = await client.post("/chat/completions", json=payload)
               
                if r.status_code == 429 and attempt + 1 < max_retries:
                    retry_after = float(r.headers.get("Retry-After", "2"))
                    await asyncio.sleep(retry_after or (2 * (attempt + 1)))
                    continue

                r.raise_for_status()
                data = r.json()
                if not isinstance(data, dict) or not data.get("choices"):
                    return {"error": f"Respuesta LLM inesperada: {str(data)[:200]}"}
                return data

        except httpx.HTTPStatusError as e:
            
            if e.response.status_code != 429 or attempt + 1 >= max_retries:
                return {"error": f"LLM HTTP {e.response.status_code}: {e.response.text[:500]}"}
            await asyncio.sleep(2 * (attempt + 1))

        except Exception as e:
            if attempt + 1 >= max_retries:
                return {"error": f"LLM error: {type(e).__name__}: {e}"}
            await asyncio.sleep(1.5 * (attempt + 1))


# ejecución de tools
async def run_tool_call(name: str, args: dict):
    try:
        if name == "calc":
            return calc(**args)
        if name == "clima":
            return await weather(**args)
        if name == "notas_agregar":
            return await note_add(**args)
        if name == "notas_listar":
            return await note_list()
        if name == "notas_borrar":
            return await note_delete(**args)
        return {"error": f"tool desconocida: {name}"}
    except Exception as e:
        return {"error": f"Fallo al ejecutar tool '{name}': {e}"}



async def ask_ai(history: list[dict], user_msg: str) -> str:
    if not OPENAI_KEY:
        return "IA desactivada (falta OPENAI_API_KEY). Podés usar comandos: /calc, /clima, /nota, /notas, /nota-borrar."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + _sanitize(history) + [
        {"role": "user", "content": user_msg}
    ]
    tools = build_tool_schemas()

  
    resp = await call_llm(messages, tools)
    if "error" in resp:
        return f"⚠️ Error al llamar al modelo: {resp['error']}\nRevisá OPENAI_API_KEY / OPENAI_MODEL / OPENAI_BASE."

    msg = resp["choices"][0].get("message", {})

  
    if msg.get("tool_calls"):
        tool_msgs = []
        for tc in msg["tool_calls"]:
            try:
                name = tc["function"]["name"]
                args_json = tc["function"].get("arguments") or "{}"
                args = json.loads(args_json)
            except Exception as e:
                tool_msgs.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "name": name if "name" in locals() else "desconocida",
                    "content": json.dumps({"error": f"args inválidos: {e}"}),
                })
                continue

            result = await run_tool_call(name, args)
            tool_msgs.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "name": name,
                "content": json.dumps(result),
            })

      
        messages += [{"role": "assistant", "tool_calls": msg["tool_calls"], "content": None}] + tool_msgs
        resp2 = await call_llm(messages, tools)
        if "error" in resp2:
            return f"⚠️ Error al finalizar respuesta: {resp2['error']}"
        return _extract_message_content(resp2)

  
    return _extract_message_content(resp)