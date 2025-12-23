
import asyncio
import websockets

async def chat_with_gateway():
    uri = "https://ai.tamer.work/Gateway/chat"
    
    async with websockets.connect(uri) as websocket:
        prompt = "What is the capital of Italy?"
        print(f"Sending prompt: {prompt}")
        
        # Send prompt to Gateway via WebSocket
        await websocket.send(prompt)
        
        # Wait for response
        response = await websocket.recv()
        print(f"Response from Gateway: {response}")

if __name__ == "__main__":
    asyncio.run(chat_with_gateway())