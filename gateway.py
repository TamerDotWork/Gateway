import uvicorn
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Imports for running external scripts
import agent   # This assumes agent.py exists and handles governance
import runpy   # This is used to run the user's script

load_dotenv()

# The API_KEY is loaded here, but it's assumed that 'minimal.py' or 'agent.py'
# will access it via os.getenv("GOOGLE_API_KEY") if they need it.
API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

# Mount static files for the dashboard
app.mount("/Gateway/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
@app.get("/Gateway/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Renders the dashboard page and executes 'minimal.py'.
    """
    target_script = "minimal.py"

    print(f"🚀 Launching {target_script} via Governance Gateway...")
    print("-" * 50)

    try:
        # Execute the target script as if it were run directly
        runpy.run_path(target_script, run_name="__main__")
        print(f"✅ {target_script} executed successfully.")
    except Exception as e:
        print(f"\n❌ Application Error during {target_script} execution: {e}")
        # You might want to log this error or display it in the dashboard template
        # for better user feedback in a production environment.

    # Render the dashboard HTML template
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5013)