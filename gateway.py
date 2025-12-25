import uvicorn
import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request ,responses
from fastapi.templating import Jinja2Templates
from google import genai
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

load_dotenv()


API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found! Make sure you have a .env file with GOOGLE_API_KEY inside.")

app = FastAPI()
client = genai.Client(api_key=API_KEY)


app.mount("/Gateway/static", StaticFiles(directory="static"), name="static") 
templates = Jinja2Templates(directory="templates")

stats = {
    "requests_from_user": 0,
    "responses_from_llm": 0,
    "errors": 0,
    "last_prompt": "None"
}


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


@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse) 
async def dashboard_page(request: Request):

    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.websocket("/")
@app.websocket("/Gateway/")
async def websocket_dashboard(websocket: WebSocket):
    await stats_manager.connect(websocket)
    try:
        while True:

            await websocket.receive_text()
    except:
        stats_manager.disconnect(websocket)


@app.websocket("/chat")
@app.websocket("/Gateway/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    global stats
    print("Chat Client Connected!")
    
    try:
        while True:

            prompt = await websocket.receive_text()
            print(f"Received Prompt: {prompt}")
            

            stats["requests_from_user"] += 1
            stats["last_prompt"] = prompt[:50] + "..."
            await stats_manager.broadcast()


            try:

                response = client.models.generate_content(
                    model="gemini-flash-latest", 
                    contents=prompt
                )
                response_text = response.text
                

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