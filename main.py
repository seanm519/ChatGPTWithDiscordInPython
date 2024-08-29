import os
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}!')

@bot.command(name='say')
async def say(ctx, *, user_message: str):
    # Defer the response to give more time for processing
    await ctx.defer()

    # Make a request to the OpenAI API
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4',
                'messages': [{'role': 'user', 'content': user_message}]
            }
        )

        response_json = response.json()
        chat_gpt_message = response_json['choices'][0]['message']['content']

        # Send the response back to Discord
        await ctx.send(chat_gpt_message)

    except Exception as e:
        await ctx.send('There was an error processing your request.')
        print(f'Error interacting with ChatGPT: {e}')

bot.run(DISCORD_TOKEN)