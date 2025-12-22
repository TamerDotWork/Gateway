import google.generativeai as genai


genai.configure(api_key="YOUR_GEMINI_API_KEY")

model = genai.GenerativeModel("gemini-flash-latest")

response = model.generate_content("Write a 3-line poem about Python programming.")

print(response.text)