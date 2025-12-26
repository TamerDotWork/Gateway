import uvicorn
import os
import sys
import runpy
import threading
import queue
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Imports for running external scripts
import agent 

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

app.mount("/Gateway/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Helper: Output Redirector ---
class OutputRedirector:
    def __init__(self, q):
        self.q = q
    def write(self, text):
        self.q.put(text)
    def flush(self):
        pass

@app.get("/", response_class=StreamingResponse)
@app.get("/Gateway/", response_class=StreamingResponse)
async def dashboard_page(request: Request):
    """
    Executes 'minimal.py' and streams the output directly into the
    Jinja2 dashboard template.
    """
    target_script = "minimal.py"
    
    # 1. Create a Queue to hold the log output
    log_queue = queue.Queue()

    # 2. Define the background worker that runs the script
    def script_worker():
        # Redirect stdout/stderr to the queue
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = OutputRedirector(log_queue)
        sys.stderr = OutputRedirector(log_queue)
        
        try:
            print(f"🚀 Launching {target_script} via Governance Gateway...")
            print("-" * 50)
            
            # Execute the user's script
            runpy.run_path(target_script, run_name="__main__")
            
            print(f"\n✅ {target_script} executed successfully.")
        except Exception as e:
            print(f"\n❌ Application Error: {e}")
        finally:
            # Restore stdout and signal end
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            log_queue.put(None) # None indicates the stream is finished

    # 3. Start the script in a separate thread so it doesn't block
    thread = threading.Thread(target=script_worker)
    thread.start()

    # 4. Define a generator that yields data to the Jinja template
    def log_generator():
        while True:
            data = log_queue.get()
            if data is None:
                break
            yield data

    # 5. Get the template object directly
    template = templates.get_template("dashboard.html")

    # 6. Stream the response. 
    # We pass 'log_generator()' as the variable 'output_stream' to the template.
    return StreamingResponse(
        template.generate(request=request, output_stream=log_generator()),
        media_type="text/html"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)