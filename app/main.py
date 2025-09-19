from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

from app.tools import calc, weather, note_add, note_list, note_delete
from app.agent import ask_ai

app = FastAPI()


app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")

@app.get("/api")
def api_home():
    return {"message": "Hola! Soy tu BOT IA + Tools 🚀"}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatInput(BaseModel):
    message: str
    history: list[ChatMessage] | None = None

@app.post("/chat")
async def chat_endpoint(inp: ChatInput):
    text = (inp.message or "").strip()
    low = text.lower()

  
    if low.startswith("/calc "):
        expr = text[6:].strip()
        try:
            res = calc(expr)
            return {"reply": f"Resultado: {res['result']}"}
        except Exception as e:
            return {"reply": f"Expresión inválida: {e}"}

    if low.startswith("/clima "):
        city = text[7:].strip()
        res = await weather(city)
        if "error" in res:
            return {"reply": f"Error: {res['error']}"}
        return {"reply": f"Clima para {res['city']}: próximas horas {res['next_hours_c']} °C"}

    if low.startswith("/nota "):
        txt = text[6:].strip()
        res = await note_add(txt)
        return {"reply": res["status"]}

    if low == "/notas":
        res = await note_list()
        if not res["notes"]:
            return {"reply": "Sin notas aún."}
        listado = "\n".join([f"- ({n['id']}) {n['text']}" for n in res["notes"]])
        return {"reply": "Notas:\n" + listado}

    if low.startswith("/nota-borrar "):
        try:
            note_id = int(text[13:].strip())
            res = await note_delete(note_id)
            return {"reply": res["status"]}
        except ValueError:
            return {"reply": "Por favor pasá un ID válido. Ej: /nota-borrar 2"}

    if low in ("/ayuda", "/comandos"):
        return {"reply": (
            "Comandos:\n"
            "• /calc 12*(3+4)\n"
            "• /clima Córdoba, AR\n"
            "• /nota comprar cables\n"
            "• /notas\n"
            "• /nota-borrar 3\n"
            "También podés hablar en lenguaje natural."
        )}

    # IA + tools
    safe_history = []
    if inp.history:
        for m in inp.history:
            r = (m.role or "").lower()
            c = (m.content or "").strip()
            if r in {"user","assistant","system"} and c:
                safe_history.append({"role": r, "content": c})

    reply = await ask_ai(safe_history, text)
    return {"reply": reply}