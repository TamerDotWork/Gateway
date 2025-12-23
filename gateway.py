from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from google import genai
import uvicorn
from typing import List

app = FastAPI()

# --- CONFIG ---
client = genai.Client(api_key="YOUR_API_KEY")

# --- STATE ---
stats = {
    "requests_from_user": 0,
    "responses_from_llm": 0,
    "errors": 0,
    "last_prompt": "None"
}

# --- STATS MANAGER ---
class StatsManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
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

# --- 1. DASHBOARD UI ---
@app.get("/")
@app.get("/Gateway/") 
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
                .status-dot { height: 10px; width: 10px; background-color: #bbb; border-radius: 50%; display: inline-block; margin-right: 5px;}
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
                <p style="text-align: center; font-size: 0.7em; color: #666; margin-top: 20px;">
                    <span id="dot" class="status-dot"></span> <span id="status-text">Connecting...</span>
                </p>
            </div>
            <script>
                // --- FIX FOR MIXED CONTENT ERROR ---
                // 1. Detect if we are on HTTPS or HTTP
                const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
                
                // 2. Build the correct URL (e.g., wss://ai.tamer.work/Gateway/)
                // This ensures we attach to the current path (/Gateway/ or /)
                const path = window.location.pathname.endsWith('/') ? window.location.pathname : window.location.pathname + '/';
                const wsUrl = `${protocol}://${window.location.host}${path}`;
                
                console.log("Connecting to WebSocket:", wsUrl);
                const ws = new WebSocket(wsUrl);

                const dot = document.getElementById("dot");
                const statusText = document.getElementById("status-text");

                ws.onopen = () => {
                    dot.style.backgroundColor = "#00ff00"; 
                    statusText.innerText = "Live Connected";
                    
                    // Keep connection alive
                    setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send("ping"); }, 1000);
                };

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    document.getElementById("req").innerText = data.requests_from_user;
                    document.getElementById("res").innerText = data.responses_from_llm;
                    document.getElementById("err").innerText = data.errors;
                    document.getElementById("last_p").innerText = data.last_prompt;
                };

                ws.onclose = () => {
                    dot.style.backgroundColor = "red";
                    statusText.innerText = "Disconnected";
                };
            </script>
        </body>
    </html>
    """

# --- 2. DASHBOARD STREAM ---
@app.websocket("/")
@app.websocket("/Gateway/")
async def websocket_dashboard(websocket: WebSocket):
    await stats_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        stats_manager.disconnect(websocket)

# --- 3. CHAT PROXY ---
@app.websocket("/chat")
@app.websocket("/Gateway/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    global stats
    
    try:
        while True:
            prompt = await websocket.receive_text()
            
            stats["requests_from_user"] += 1
            stats["last_prompt"] = prompt[:50]
            await stats_manager.broadcast()

            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=prompt
                )
                await websocket.send_text(response.text)
                
                stats["responses_from_llm"] += 1
                await stats_manager.broadcast()
            except Exception as e:
                stats["errors"] += 1
                await websocket.send_text(f"Error: {str(e)}")
                await stats_manager.broadcast()

    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)