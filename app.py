from google import genai



client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-flash-latest", 
    contents="What is the capital of France?"
)

print(response.text)