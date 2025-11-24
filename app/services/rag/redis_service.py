import redis.asyncio as redis
import json
from typing import List, Dict

import os
from dotenv import load_dotenv

load_dotenv()

class RedisService:
    def __init__(self):
        host=os.getenv("REDIS_HOST", "localhost")
        port=int(os.getenv("REDIS_PORT", 6379))

        print(f"🔌 RedisService connecting to {host}:{port}")

        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True
        )

    async def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        print(f"📖 Getting history for session: {session_id}")
        try:
            history = await self.client.get(f"chat:{session_id}")
            result = json.loads(history) if history else []
            print(f"✅ Retrieved {len(result)} messages")
            return result
        except Exception as e:
            print(f"❌ Redis get_chat_history error: {e}")
            raise

    async def add_message(self, session_id: str, message: List[Dict[str, str]], ttl: int = 3600):
        """ Add Multiple Msg to Chat History, ttl = time to live"""
        print(f"💾 Saving {len(message)} messages for session: {session_id}")  # ✅ Debug
        try:
            history = await self.get_chat_history(session_id)
            history.extend(message)
            await self.client.set(
                f"chat:{session_id}",
                json.dumps(history),
                ex=ttl
            )
            print("✅ Messages saved to Redis")
        except Exception as e:
            print(f"❌ Redis add_message error: {e}")
            raise

    async def clear_session(self, session_id: str):
        await self.client.delete(f"chat:{session_id}")

    async def close(self):
        await self.client.aclose()