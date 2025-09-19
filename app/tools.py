# app/tools.py
import ast, operator, httpx, unicodedata

# CALCULADORA sin API
def _safe_eval(expr: str):
    allowed = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.USub: operator.neg
    }
    def _eval(node):
        if isinstance(node, ast.Num): return node.n
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed:
            return allowed[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in allowed:
            return allowed[type(node.op)](_eval(node.left), _eval(node.right))
        raise ValueError("Expresión no permitida")
    return _eval(ast.parse(expr, mode="eval").body)

def calc(expr: str):
    return {"result": _safe_eval(expr)}

#  CLIMA (Open-Meteo, sin API key)
def _norm(s: str) -> str:
    
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

async def weather(city: str):
    """
    Devuelve próximas horas en °C usando Open-Meteo.
    Estrategia de búsqueda:
      1) Prueba la entrada tal cual
      2) Normaliza (sin acentos)
      3) Usa solo la primera parte (antes de la coma)
    Pide hasta 10 resultados y elige el mejor:
      - país AR puntúa más
      - si el usuario escribió provincia, puntúa esa admin1
      - coincidencia del nombre suma
    """
    raw = (city or "").strip()
    if not raw:
        return {"error": "Decime una ciudad. Ej: 'Córdoba, AR' o 'Corral de Bustos, Córdoba, AR'."}

    # Partes para inferir provincia (si vino)
    parts_raw = [p.strip() for p in raw.split(",")]
    province_hint = parts_raw[1].lower() if len(parts_raw) >= 2 else None

    
    q1 = raw                       
    q2 = _norm(raw)                
    q3 = _norm(parts_raw[0])       
    queries = [q1, q2, f"{q3}, Argentina", q3]

    async with httpx.AsyncClient(timeout=20) as client:
        results = []
        for q in queries:
            try:
                r = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": q, "count": 10, "language": "es"},
                )
                r.raise_for_status()
                data = r.json()
                if data.get("results"):
                    results = data["results"]
                    break
            except Exception:
               
                continue

        if not results:
            return {"error": f"Ciudad no encontrada: {raw}. Probá 'Ciudad, Provincia, AR'."}

       
        raw_lower = raw.lower()

        def score(r):
            s = 0
            if r.get("country_code") == "AR":
                s += 10
            if province_hint and r.get("admin1", "").lower().startswith(province_hint):
                s += 5
            name_l = (r.get("name") or "").lower()
            if name_l and name_l in raw_lower:
                s += 2
            return s

        best = max(results, key=score)
        lat, lon = best["latitude"], best["longitude"]
        label = f"{best.get('name')}, {best.get('admin1','')}, {best.get('country_code','')}"

        fw = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m",
                "forecast_days": 1,
                "timezone": "auto",
            },
        )
        fw.raise_for_status()
        temps = (fw.json().get("hourly", {}).get("temperature_2m") or [])[:6]
        if not temps:
            return {"error": f"Sin datos de temperatura para {label}."}

        return {"city": label, "next_hours_c": temps}

# NOTAS (SQLite vía db.py)
from .db import add_note as _add, list_notes as _list, delete_note as _delete

async def note_add(text: str):
    return {"status": _add(text)}

async def note_list():
    return {"notes": _list()}

async def note_delete(note_id: int):
    return {"status": _delete(note_id)}