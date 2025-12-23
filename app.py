import asyncio
import websockets

async def chat_with_gateway():
    # 1. Use wss:// for secure connections (required if your site is https)
    # 2. Ensure the path matches your reverse proxy settings.
    #    - If testing locally: "ws://localhost:5013/chat"
    #    - If live on server:  "wss://ai.tamer.work/Gateway/chat"
    uri = "wss://ai.tamer.work/Gateway/chat"
    
    print(f"Attempting to connect to: {uri}")

    try:
        # ssl=True is usually handled automatically by wss:// scheme, 
        # but connection logic ensures it works.
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            prompt = "What is the capital of Italy?"
            print(f"Sending prompt: {prompt}")
            
            # Send prompt to Gateway via WebSocket
            await websocket.send(prompt)
            
            # Wait for response
            print("Waiting for response...")
            response = await websocket.recv()
            print(f"Response from Gateway: {response}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(chat_with_gateway())