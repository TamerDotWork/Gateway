import google.generativeai as genai
 
import os
from dotenv import load_dotenv
 
 

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found! Make sure you have a .env file with GOOGLE_API_KEY inside.")

# 1. Setup
genai.configure(api_key=API_KEY)

# 2. Select Model (Gemini 1.5 Flash is fast and efficient)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. Ask Question
prompt = "Explain quantum computing in one sentence."
response = model.generate_content(prompt)

# 4. Print Response
print(response.text)