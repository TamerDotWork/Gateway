import uvicorn
import os
import sys
import runpy
import threading
import queue
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Imports for running external scripts
import agent 

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

app.mount("/Gateway/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Custom Class to Redirect Print to Queue ---
class OutputRedirector:
    def __init__(self, q):
        self.q = q

    def write(self, text):
        # Determine if we should flush immediately
        self.q.put(text)

    def flush(self):
        pass

# --- The Generator that streams data ---
def script_output_generator(target_script):
    log_queue = queue.Queue()
    
    def run_script_in_thread():
        # Capture existing stdout so we can restore it later
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # Redirect stdout/stderr to our queue wrapper
        sys.stdout = OutputRedirector(log_queue)
        sys.stderr = OutputRedirector(log_queue)
        
        try:
            log_queue.put(f"🚀 Launching {target_script} via Governance Gateway...\n")
            log_queue.put("-" * 50 + "\n")
            
            # Run the script
            runpy.run_path(target_script, run_name="__main__")
            
            log_queue.put(f"\n✅ {target_script} executed successfully.\n")
        except Exception as e:
            log_queue.put(f"\n❌ Application Error: {e}\n")
        finally:
            # Restore stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            # Signal the end of the stream
            log_queue.put(None)

    # Start the script in a separate thread so it doesn't block the stream
    thread = threading.Thread(target=run_script_in_thread)
    thread.start()

    # Yield data from queue as it arrives
    while True:
        data = log_queue.get()
        if data is None:
            break
        yield data

@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Renders the static dashboard. The JS inside will trigger the script execution.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/run-script")
async def run_script():
    """
    Endpoint called by JS to stream the output.
    """
    return StreamingResponse(
        script_output_generator("minimal.py"), 
        media_type="text/plain"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)