import uvicorn
import os
import sys
import runpy
import threading
import queue
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

# --- Redirector Class ---
class OutputRedirector:
    def __init__(self, q):
        self.q = q
    def write(self, text):
        self.q.put(text)
    def flush(self):
        pass

# --- Generator Function ---
def script_output_generator(target_script):
    log_queue = queue.Queue()
    
    def run_script_in_thread():
        # Capture standard output
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # Redirect to our queue
        sys.stdout = OutputRedirector(log_queue)
        sys.stderr = OutputRedirector(log_queue)
        
        try:
            log_queue.put(f"🚀 Initializing {target_script}...\n")
            log_queue.put("-" * 50 + "\n")
            
            # Run the user script
            runpy.run_path(target_script, run_name="__main__")
            
            log_queue.put(f"\n✅ {target_script} finished successfully.\n")
        except Exception as e:
            log_queue.put(f"\n❌ Execution Error: {e}\n")
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            log_queue.put(None) # Signal end

    # Start thread
    thread = threading.Thread(target=run_script_in_thread)
    thread.start()

    # Yield output to the browser as it becomes available
    while True:
        data = log_queue.get()
        if data is None:
            break
        yield data

@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Renders the HTML container first.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/stream-script")
async def stream_script():
    """
    The JS calls this automatically to get the live log stream.
    """
    return StreamingResponse(
        script_output_generator("minimal.py"), 
        media_type="text/plain"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)