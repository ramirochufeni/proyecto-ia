import sqlite3, os
DB_PATH = os.getenv("DB_PATH", "bot.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, text TEXT)")
    return conn

def add_note(text: str):
    with get_conn() as c:
        c.execute("INSERT INTO notes(text) VALUES (?)", (text,))
    return "Nota guardada."

def list_notes():
    with get_conn() as c:
        rows = c.execute("SELECT id, text FROM notes ORDER BY id DESC LIMIT 10").fetchall()
    return [{"id": r[0], "text": r[1]} for r in rows]

def delete_note(note_id: int):
    with get_conn() as c:
        cur = c.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        if cur.rowcount == 0:
            return "No se encontró ninguna nota con ese ID."
    return f"Nota {note_id} eliminada."
