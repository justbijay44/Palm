# test_redis_wsl.py
import asyncio
import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    
    print(f"🔌 Connecting to Redis at {host}:{port}")
    
    try:
        client = redis.Redis(host=host, port=port, decode_responses=True)
        
        # Test ping
        pong = await client.ping()
        print(f"✅ Ping successful: {pong}")
        
        # Test set/get
        await client.set("test", "hello")
        value = await client.get("test")
        print(f"✅ Set/Get test: {value}")
        
        await client.close()
        print("✅ Redis connection working!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Check Redis is running in WSL: redis-cli ping")
        print(f"2. Check WSL IP is correct: hostname -I")
        print(f"3. Check Redis binds to 0.0.0.0 (not just 127.0.0.1)")

asyncio.run(test())