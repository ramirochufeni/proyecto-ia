# 🤖 BOT IA + Tools

Un chatbot en **español** hecho con [FastAPI](https://fastapi.tiangolo.com/) y la API de OpenAI.  
Incluye **herramientas integradas (tools)** que permiten:

- 📐 **Calculadora** → realiza operaciones aritméticas seguras.  
- 🌦️ **Clima** → consulta el pronóstico de cualquier ciudad usando [Open-Meteo](https://open-meteo.com/).  
- 📝 **Notas** → agrega, lista y elimina notas persistentes en SQLite.  
- 💬 **IA** → conversación natural, combinando las tools cuando es necesario.  

---

## 🚀 Demo

La interfaz web incluida permite probarlo fácilmente:  

http://127.0.0.1:8000

Desde allí podés:
- Escribir mensajes al bot.  
- Probar comandos como:  
  - `/calc 12*(3+4)`  
  - `/clima Córdoba, AR`  
  - `/nota comprar cables`  
  - `/notas`  
  - `/nota-borrar 1`

---

## 📂 Estructura del proyecto

proyecto-ia/
│── app/ # Backend FastAPI + lógica del bot
│── web/ # Interfaz web (HTML/JS/CSS)
│── bot.db # Base de datos SQLite (se crea al correr)
│── requirements.txt
│── .env.example # Variables de entorno de ejemplo
│── README.md


---

## ⚙️ Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/ramirochufeni/proyecto-ia.git
   cd proyecto-ia
Crear un entorno virtual e instalar dependencias:

bash
Copiar código
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Crear un archivo .env copiando el ejemplo:

Copiar código
cp .env.example .env
Editar y completar con tu propia clave:

ini
Copiar código
OPENAI_API_KEY=tu_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE=https://api.openai.com/v1
▶️ Ejecución
Correr el servidor con:

Copiar código
uvicorn app.main:app --reload
Abrir en el navegador:

Copiar código
http://127.0.0.1:8000
📌 Tecnologías usadas
FastAPI

Uvicorn

HTTPX

SQLite

OpenAI API

✨ Autor
👨‍💻 Ramiro Chufeni

🌐 GitHub

📱 Instagram: @rami.chufeni

📧 ramirochufeni@gmail.com

