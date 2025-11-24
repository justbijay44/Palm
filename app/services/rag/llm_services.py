import os
from groq import Groq
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class LLMServices:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    async def generate_response(self, messages:  List[Dict[str,str]], temperature: float = 0.7) -> str:
        """
        messages = {'role': 'system/user/assistant', 'content': "message"}
        temperature : 0 - 1 -> towards 0 means more accurate + predictable, towards 1 means more creative + varied
        """
        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                temperature = temperature,
                max_tokens = 1000
            )
            return response.choices[0].message.content
        
        except Exception as e:
            raise Exception(f"LLM generation failed {str(e)}")