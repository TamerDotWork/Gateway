import google.generativeai as genai

# 1. Setup your API Key
# Get one for free at: https://aistudio.google.com/
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# 2. Initialize the model (gemini-1.5-flash is fast and cost-effective)
model = genai.GenerativeModel("gemini-flash-latest")

# 3. Generate a response
response = model.generate_content("Write a 3-line poem about Python programming.")

# 4. Print the result
print(response.text)