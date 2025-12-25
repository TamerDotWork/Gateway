# chat.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("API Key not found!")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

prompt = "Explain quantum computing in one sentence."
response = model.generate_content(prompt)

print(response.text)