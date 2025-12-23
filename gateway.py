# gateway.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from google import genai
import uvicorn
from typing import List

app = FastAPI()

# --- CONFIG ---
# Replace with your actual API Key
client = genai.Client(api_key="YOUR_API_KEY")

# --- STATE ---
stats = {
    "requests_from_user": 0,
    "responses_from_llm": 0,
    "errors": 0,
    "last_prompt": "None"
}

# --- STATS BROADCASTER ---
class StatsManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await websocket.send_json(stats) # Send initial data

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self):
        for connection in self.active_connections:
            try:
                await connection.send_json(stats)
            except:
                pass

stats_manager = StatsManager()

# --- 1. DASHBOARD UI (Browser) ---
@app.get("/", response_class=HTMLResponse)
async def dashboard_page():
    return """
    <html>
        <head>
            <title>LLM Gateway Monitor</title>
            <style>
                body { font-family: sans-serif; background: #1a1a1a; color: white; display: flex; justify-content: center; padding-top: 50px; }
                .card { background: #2d2d2d; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 400px; }
                h1 { color: #00ffcc; border-bottom: 1px solid #444; padding-bottom: 10px; }
                .stat { font-size: 1.2em; margin: 10px 0; display: flex; justify-content: space-between; }
                .value { font-weight: bold; color: #ffcc00; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Gateway Stats</h1>
                <div class="stat"><span>User Requests:</span> <span id="req" class="value">0</span></div>
                <div class="stat"><span>LLM Responses:</span> <span id="res" class="value">0</span></div>
                <div class="stat"><span>Total Errors:</span> <span id="err" class="value" style="color: red;">0</span></div>
                <hr>
                <div style="font-size: 0.8em; color: #888;">
                    <strong>Last Prompt:</strong><br> <span id="last_p">None</span>
                </div>
                <p style="text-align: center; font-size: 0.7em; color: #666;">🟢 Real-time WebSocket Stream</p>
            </div>
            <script>
                // Connect to the WebSocket at the same URI path "/"
                const ws = new WebSocket(`ws://${window.location.host}/`);
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    document.getElementById("req").innerText = data.requests_from_user;
                    document.getElementById("res").innerText = data.responses_from_llm;
                    document.getElementById("err").innerText = data.errors;
                    document.getElementById("last_p").innerText = data.last_prompt;
                };
            </script>
        </body>
    </html>
    """

# --- 2. DASHBOARD DATA STREAM (WS /) ---
@app.websocket("/")
async def websocket_dashboard(websocket: WebSocket):
    await stats_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        stats_manager.disconnect(websocket)

# --- 3. CHAT PROXY (WS /chat) ---
@app.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    global stats
    
    try:
        while True:
            # Receive prompt from app.py
            prompt = await websocket.receive_text()
            
            # Update stats
            stats["requests_from_user"] += 1
            stats["last_prompt"] = prompt[:50]
            await stats_manager.broadcast() # Update Dashboard

            try:
                # Call Gemini
                response = client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=prompt
                )
                
                # Send text back to app.py
                await websocket.send_text(response.text)
                
                # Update stats
                stats["responses_from_llm"] += 1
                await stats_manager.broadcast() # Update Dashboard

            except Exception as e:
                stats["errors"] += 1
                await websocket.send_text(f"Error: {e}")
                await stats_manager.broadcast()

    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)