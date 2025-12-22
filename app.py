import requests

# Point to your Middleman/Gateway instead of Google
GATEWAY_URL = "https://ai.tamer.work/Gateway/chat"

def ask_question(text):
    payload = {"contents": text}
    response = requests.post(GATEWAY_URL, json=payload)
    print("Response:", response.json().get("text", "Error"))

# Send some test requests
ask_question("What is the capital of France?")
ask_question("How do you bake a cake?")