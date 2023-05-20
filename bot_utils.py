import aiohttp
import json
import openai
from config import OPENAI_API_KEY

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

async def generate_response(messages):
    """
    Helper function to call the OpenAI API.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    payload = json.dumps({
        "model": "gpt-4",
        "messages": messages,
        "max_tokens": 2048,
        "temperature": .05,
        "top_p": 1,
    })

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(url, headers=headers, data=payload) as resp:
                response_data = await resp.json()
                message = response_data['choices'][0]['message']['content'].strip()
                return message
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return None
