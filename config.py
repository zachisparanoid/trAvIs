import os
from dotenv import load_dotenv

def load_env_vars():
    load_dotenv()
    global OPENAI_API_KEY, DISCORD_BOT_TOKEN
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_TOKEN')

load_env_vars()
