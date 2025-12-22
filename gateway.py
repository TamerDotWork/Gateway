from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from google import genai
import uvicorn

app = FastAPI()

# Internal Stats Store
stats = {
    "requests_from_user": 0,
    "responses_from_llm": 0,
    "errors": 0,
    "last_prompt": "None"
}

# Initialize LLM Client
# Replace with your actual API Key
client = genai.Client(api_key="YOUR_API_KEY")

@app.post("/chat")
async def proxy_chat(request: Request):
    global stats
    stats["requests_from_user"] += 1
    
    # Get prompt from the user application
    data = await request.json()
    prompt = data.get("contents", "")
    stats["last_prompt"] = prompt[:50] + "..." if len(prompt) > 50 else prompt

    try:
        # Forward to Gemini
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        stats["responses_from_llm"] += 1
        return {"text": response.text}
    
    except Exception as e:
        stats["errors"] += 1
        return {"error": str(e)}

# --- DASHBOARD SECTION ---
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """A simple HTML page that auto-refreshes every 2 seconds"""
    return f"""
    <html>
        <head>
            <title>LLM Gateway Monitor</title>
            <meta http-equiv="refresh" content="2">
            <style>
                body {{ font-family: sans-serif; background: #1a1a1a; color: white; display: flex; justify-content: center; padding-top: 50px; }}
                .card {{ background: #2d2d2d; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 400px; }}
                h1 {{ color: #00ffcc; border-bottom: 1px solid #444; padding-bottom: 10px; }}
                .stat {{ font-size: 1.2em; margin: 10px 0; display: flex; justify-content: space-between; }}
                .value {{ font-weight: bold; color: #ffcc00; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Gateway Stats</h1>
                <div class="stat"><span>Total User Requests:</span> <span class="value">{stats['requests_from_user']}</span></div>
                <div class="stat"><span>Total LLM Responses:</span> <span class="value">{stats['responses_from_llm']}</span></div>
                <div class="stat"><span>Total Errors:</span> <span class="value" style="color: red;">{stats['errors']}</span></div>
                <hr>
                <div style="font-size: 0.8em; color: #888;">
                    <strong>Last Prompt:</strong><br> {stats['last_prompt']}
                </div>
                <p style="text-align: center; font-size: 0.7em; color: #666;">Auto-refreshing every 2s...</p>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Start the gateway on port 8000
    uvicorn.run(app, host="0.0.0.0", port=5013)