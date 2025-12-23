import asyncio
import websockets

async def chat_with_gateway():
    # ERROR FIX: Changed https:// to wss://
    # NOTE: Ensure the path matches your server route or proxy configuration
    uri = "wss://ai.tamer.work/Gateway/chat" 
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            prompt = "What is the capital of Italy?"
            print(f"Sending prompt: {prompt}")
            
            # Send prompt to Gateway via WebSocket
            await websocket.send(prompt)
            
            # Wait for response
            response = await websocket.recv()
            print(f"Response from Gateway: {response}")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(chat_with_gateway())