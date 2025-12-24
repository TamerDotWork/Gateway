import uvicorn
import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from google import genai
from typing import List
from fastapi.staticfiles import StaticFiles  # <--- 1. IMPORT THIS
from fastapi.responses import HTMLResponse  # <--- ADD THIS

# --- CONFIGURATION ---
# 1. Load environment variables from .env file
load_dotenv()

# 2. Retrieve API Key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found! Make sure you have a .env file with GOOGLE_API_KEY inside.")
app = FastAPI()

templates = Jinja2Templates(directory="templates")


if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("static/css"):
    os.makedirs("static/css")
if not os.path.exists("static/js"):
    os.makedirs("static/js")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- GLOBAL STATE ---
stats = {
    "requests_from_user": 0,
    "responses_from_llm": 0,
    "errors": 0,
    "last_prompt": "None"
}

# --- CONNECTION MANAGER ---
class StatsManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial stats immediately upon connection
        await websocket.send_json(stats)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self):
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(stats)
            except:
                self.disconnect(connection)

stats_manager = StatsManager()

# --- 1. DASHBOARD PAGE (Jinja) ---
@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse) 
async def dashboard_page(request: Request):
    # Returns the HTML file using Jinja2
    return templates.TemplateResponse("dashboard.html", {"request": request})

# --- 2. DASHBOARD DATA STREAM ---
@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse) 
async def websocket_dashboard(websocket: WebSocket):
    await stats_manager.connect(websocket)
    try:
        while True:
            # Keep connection open, ignore incoming text (like "ping")
            await websocket.receive_text()
    except:
        stats_manager.disconnect(websocket)

# --- 3. CHAT BOT ENDPOINT ---
@app.websocket("/chat")
@app.websocket("/Gateway/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    global stats
    print("Chat Client Connected!")
    
    try:
        while True:
            # 1. Receive Prompt
            prompt = await websocket.receive_text()
            print(f"Received Prompt: {prompt}")
            
            # Update Stats
            stats["requests_from_user"] += 1
            stats["last_prompt"] = prompt[:50] + "..."
            await stats_manager.broadcast()

            # 2. Call Google AI
            try:
                # Synchronous call wrapped in async if needed
                response = client.models.generate_content(
                    model="gemini-flash-latest", 
                    contents=prompt
                )
                response_text = response.text
                
                # 3. Send Response
                await websocket.send_text(response_text)
                stats["responses_from_llm"] += 1
                await stats_manager.broadcast()
                
            except Exception as e:
                print(f"AI Error: {e}")
                stats["errors"] += 1
                await websocket.send_text(f"Error processing request: {str(e)}")
                await stats_manager.broadcast()

    except WebSocketDisconnect:
        print("Chat Client Disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)