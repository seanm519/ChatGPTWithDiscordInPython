import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import requests
import asyncio

load_dotenv()  # Load environment variables from .env file

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

intents = discord.Intents.default()
intents.message_content = True  # Allow bot to read message content
intents.guilds = True
intents.members = True  # Enable the intent to read members
intents.dm_messages = True  # Enable DMs handling

bot = commands.Bot(command_prefix='/', intents=intents)

# Queue to handle incoming messages
message_queue = asyncio.Queue()
queue_processing = asyncio.Event()

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    await setup()  # Call setup function when bot is ready

# Helper function to send DMs
async def send_dm(user: discord.User, message: str):
    try:
        await user.send(message)
        print(f"Sent DM to {user.name}")
    except discord.Forbidden:
        print(f"Cannot send DM to {user.name}, they might have DMs disabled.")

async def process_queue():
    while True:
        print("Waiting for queue to be processed...")
        await queue_processing.wait()  # Wait for queue_processing event
        print("Processing queue...")
        while not message_queue.empty():
            user, interaction, message = await message_queue.get()
            print(f"Processing message from {user.display_name}: {message}")
            await handle_message(user, interaction, message)
        queue_processing.clear()  # Clear the event after processing
        print("Queue processed, waiting for new tasks...")

async def handle_message(user, interaction, message):
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

        # Send the user's question and bot's response back to the channel
        await interaction.followup.send(f"{user.display_name} asked: {message}\n\nBot response: {chat_gpt_message}")

        # Optionally, send a DM to the user with the response
        await send_dm(user, f"Here is your response from ChatGPT: {chat_gpt_message}")

    except Exception as e:
        await interaction.followup.send('There was an error processing your request.')
        print(f'Error interacting with ChatGPT: {e}')

# Registering the /say command with channel-based access control and queue functionality
@bot.tree.command(name="say")
async def say(interaction: discord.Interaction, *, message: str):
    # Check if the command is issued in the "help" channel
    if isinstance(interaction.channel, discord.TextChannel) and interaction.channel.name != "help":
        await interaction.response.send_message("Please use the 'help' channel to interact with the bot.", ephemeral=True)
        return

    user = interaction.user  # Get the user who invoked the command

    # Defer the response to let Discord know the bot will take some time
    await interaction.response.defer()

    # Add the user's message to the queue
    await message_queue.put((user, interaction, message))

    # Trigger the event loop to start processing the queue
    queue_processing.set()

# Handle direct messages (DMs)
@bot.event
async def on_message(message):
    # Only respond to DMs, ignore guild messages (since we are controlling those with commands)
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        user_message = message.content
        
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

            # Send the response back as a DM to the user
            await message.author.send(chat_gpt_message)

        except Exception as e:
            await message.author.send('There was an error processing your request.')
            print(f'Error interacting with ChatGPT: {e}')

    # Ensure bot processes regular commands like /say
    await bot.process_commands(message)

# Setup to initiate the queue processing task when the bot is ready
async def setup():
    bot.loop.create_task(process_queue())

async def main():
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("Bot stopped manually")
    finally:
        await bot.close()

# Run the asynchronous main function
asyncio.run(main())