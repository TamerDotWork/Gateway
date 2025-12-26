import uvicorn
import os
import io
import contextlib
import runpy
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Imports for running external scripts
import agent   # This assumes agent.py exists and handles governance

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found!")

app = FastAPI()

app.mount("/Gateway/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# --- GLOBAL STATE ---
stats = {
    "requests_from_user": 0,
    "responses_from_llm": 0,
    "errors": 0,
    "last_prompt": "None",
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "total_tokens_used": 0,
}

@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse)
async def main_action(request: Request):
    
    target = "minimal.py"
    
    # Create a string buffer to capture output
    log_capture_string = io.StringIO()

    # 2. Call Google AI
    try:
        # Synchronous call wrapped in async if needed
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=prompt
        )
        response_text = response.text
        
        # Add token counting:
        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.candidates_token_count
        total_tokens = response.usage_metadata.total_token_count


        # 3. Send Response
        await websocket.send_text(response_text)
        stats["responses_from_llm"] += 1
        stats["total_input_tokens"] += input_tokens
        stats["total_output_tokens"] += output_tokens
        stats["total_tokens_used"] += total_tokens
        await stats_manager.broadcast()

        
    except Exception as e:
        print(f"AI Error: {e}")
        stats["errors"] += 1
        await websocket.send_text(f"Error processing request: {str(e)}")
        await stats_manager.broadcast()

        try:
            # Execute the target script
            # Any print statements inside minimal.py will now go to log_capture_string
            runpy.run_path(target)
           
        except Exception as e:
            print(f"\n❌ \n execution: {e}")

    # Get the captured content as a string
    execution_logs = log_capture_string.getvalue()
    
    # Close the buffer
    log_capture_string.close()

    # Pass the logs to the template
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "execution_logs": execution_logs
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)