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

@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Renders the dashboard page and executes 'minimal.py',
    capturing the output to display in the template.
    """
    target_script = "minimal.py"
    
    # Create a string buffer to capture output
    log_capture_string = io.StringIO()

    # Redirect stdout and stderr to our string buffer
    with contextlib.redirect_stdout(log_capture_string), contextlib.redirect_stderr(log_capture_string):
        print(f"🚀 Launching {target_script} via Governance Gateway...")
        print("-" * 50)

        try:
            # Execute the target script
            # Any print statements inside minimal.py will now go to log_capture_string
            runpy.run_path(target_script)
            print(f"✅ {target_script} executed successfully.")
        except Exception as e:
            print(f"\n❌ Application Error during {target_script} execution: {e}")

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