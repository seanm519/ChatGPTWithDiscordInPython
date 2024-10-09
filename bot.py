import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests
import aiohttp
import asyncio
from collections import deque

load_dotenv()  # Load environment variables from .env file

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

intents = discord.Intents.default()
intents.message_content = True  # Allow bot to read message content

bot = commands.Bot(command_prefix='/', intents=intents)

# Create a deque (double-ended queue) to store user questions
question_queue = deque()

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}!')

    # Semaphore to limit the number of concurrent API requests
semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests (you can adjust this)

# Function to make request to OpenAI
async def ask_openai(question: str):
    async with semaphore:  # Only allow a limited number of concurrent requests
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {OPENAI_API_KEY}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'gpt-4',
                        'messages': [{'role': 'user', 'content': question}]
                    }
                ) as response:
                    response_json = await response.json()
                    return response_json['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error contacting OpenAI: {e}")
            return "There was an error contacting ChatGPT."

# Background task that processes the question queue
async def process_queue():
    while True:
        if question_queue:
            question, interaction = question_queue.popleft()  # Get the oldest question from the queue
            gpt_response = await ask_openai(question)  # Send the question to ChatGPT

            # Send the ChatGPT response as a new message to the channel
            await interaction.channel.send(f"{interaction.user.display_name}'s ChatGPT response: {gpt_response}")
        
        await asyncio.sleep(1)  # Check the queue every 10 seconds

# /say command that adds a question to the queue
@bot.tree.command(name="say")
async def say(interaction: discord.Interaction, *, message: str):
    user = interaction.user  # Get the user who invoked the command
    channel = interaction.channel  # Get the channel where the command was invoked

    # Respond immediately with "Processing..." to complete the interaction
    await interaction.response.send_message("Processing...")

    # Add the question and interaction object to the queue
    question_queue.append((message, interaction))

# Start the background task when the bot is ready
@bot.event
async def on_ready():
    bot.loop.create_task(process_queue())  # Start the queue processor
    print(f'Bot is online as {bot.user}!')

async def main():
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("Bot stopped manually")
    finally:
        await bot.close()

# Run the asynchronous main function
asyncio.run(main())