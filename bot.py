import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import requests

load_dotenv()  # Load environment variables from .env file

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

intents = discord.Intents.default()
intents.message_content = True  # Allow bot to read message content
intents.guilds = True
intents.members = True  # Enable the intent to read members

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

# Registering the /say command with channel-based access control
@bot.tree.command(name="say")
async def say(interaction: discord.Interaction, *, message: str):
    # Check if the command is issued in the "help" channel
    if interaction.channel.name != "help":
        await interaction.response.send_message("Please use the help channel to interact with the bot.", ephemeral=True)
        return

    # Defer the response to give more time for processing
    await interaction.response.defer()

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
                'messages': [{'role': 'user', 'content': message}]
            }
        )

        response_json = response.json()
        chat_gpt_message = response_json['choices'][0]['message']['content']

        # Send the response back to Discord
        await interaction.followup.send(chat_gpt_message)

    except Exception as e:
        await interaction.followup.send('There was an error processing your request.')
        print(f'Error interacting with ChatGPT: {e}')

bot.run(DISCORD_TOKEN)