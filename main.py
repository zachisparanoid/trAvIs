# main.py
import aiohttp
import logging
import asyncio
import discord
import os
import re
from discord.ext import commands
from datetime import datetime
from collections import defaultdict
from config import DISCORD_BOT_TOKEN, OPENAI_API_KEY, load_env_vars
from db import insert_message_to_db, load_annoy_index, conn, cursor
from response_conditions import should_bot_chime_in
from bot_utils import generate_response

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, description="A conversational bot")

# Load environment variables
load_env_vars()

# Load the Annoy index
annoy_index = load_annoy_index()

# Global variable for the toggle_mention function
only_respond_to_mentions = False

@bot.command(name='toggle_mention')
async def toggle_mention(ctx):
    global only_respond_to_mentions
    only_respond_to_mentions = not only_respond_to_mentions
    await ctx.send(f'Toggle successful. only_respond_to_mentions is now set to {only_respond_to_mentions}.')

@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')

@bot.event
async def close():
    if conn:
        cursor.close()
        conn.close()
    await super().close()

@bot.event
async def on_message(message):
    # If bot is mentioned directly, it will respond
    if message.author == bot.user or message.content.startswith('!'):
        await bot.process_commands(message)
        return

    if only_respond_to_mentions and not bot.user.mentioned_in(message):
        return

    if isinstance(message.channel, discord.DMChannel):
        channel_id = f"dm-{message.author.id}"
    elif message.reference and message.reference.resolved:
        channel_id = f"thread-{message.channel.id}"
    else:
        channel_id = message.channel.id

    insert_message_to_db(channel_id, "user", message.content)

    # Get bot's decision and print to terminal
    score, should_respond = should_bot_chime_in(message.content, message.author.id, channel_id)
    print(f"Bot's score: {score}")
    print(f"Bot's decision: {'Respond' if should_respond else 'Do not respond'}")

    if should_respond:
        cursor.execute("SELECT role, content FROM message_history WHERE channel_id = ? ORDER BY timestamp DESC LIMIT 20", (channel_id,))
        recent_messages = cursor.fetchall()[::-1]
        messages = [{"role": "system", "content": "You are a sassy conversational bot with a sense of sarcasm. Try to be short with your responses, if you feel like it. do not offer assistance or ask users if they have any questions, they can do it themselves. You're sort of a dick to people."}] + [{"role": row[0], "content": row[1]} for row in recent_messages]
        response = await generate_response(messages)

        if response:
            insert_message_to_db(channel_id, "assistant", response)
            async with message.channel.typing():
                await asyncio.sleep(2)
                await message.channel.send(response[:2048])

            logging.debug(f"Channel ID: {channel_id}")
            logging.debug(f"User Message: {message.content}")
            logging.debug(f"Assistant's Response: {response}")
            logging.debug(f"Message History Length: {len(recent_messages)}")
            logging.debug(f"Recent Messages: {recent_messages}\n")

    last_response_time = datetime.now()

@bot.event
async def on_disconnect():
    pass

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
