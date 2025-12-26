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
# start.py
import agent   # This runs your governance code
import runpy   # This runs the user's script
import sys

 
load_dotenv()

# 2. Retrieve API Key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found! Make sure you have a .env file with GOOGLE_API_KEY inside.")

app = FastAPI()
client = genai.Client(api_key=API_KEY)


app.mount("/Gateway/static", StaticFiles(directory="static"), name="static") 
templates = Jinja2Templates(directory="templates")


 
@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse) 
async def dashboard_page(request: Request):


    try:
        ns = runpy.run_path("minimal.py")

        # Expect the script to define OUTPUT variable
        result = ns.get("OUTPUT", "No return value found")
        print(result)
    except Exception as e:
        result = f"❌ Application Error: {str(e)}"

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "result": result}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)