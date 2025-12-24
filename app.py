import asyncio
import websockets

async def chat_with_gateway():
    uri = "wss://ai.tamer.work/Gateway/chat"
    
    print(f"Connecting to: {uri} ...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            prompt = "What is the capital of Italy?"
            print(f"📤 Sending: {prompt}")
            
            await websocket.send(prompt)
            
            print("⏳ Waiting for AI response...")
            response = await websocket.recv()
            
            print("-" * 30)
            print(f"🤖 AI Response:\n{response}")
            print("-" * 30)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(chat_with_gateway())