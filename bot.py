import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
import asyncio
from collections import deque
from PIL import Image
import pytesseract
import io

load_dotenv()  # Load environment variables from .env file

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

intents = discord.Intents.default()
intents.message_content = True  # Allow bot to read message content
intents.messages = True  # Allow bot to listen for messages

bot = commands.Bot(command_prefix='/', intents=intents)

# Create a deque (double-ended queue) to store user questions
question_queue = deque()

# Semaphore to limit the number of concurrent API requests
semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests

# Function to make an asynchronous request to OpenAI
async def ask_openai(question: str):
    async with semaphore:  # Only allow a limited number of concurrent requests
        try:
            # Prepend the assistant prompt to every message
            assistant_prompt = "You are a teaching assistant in a college class designed to answer student questions. Structure your responses in a way that students can learn from these answers, like providing examples or in-depth explanations."
            full_prompt = f'{assistant_prompt}\n\nStudentQuestion: "{question}"'

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {OPENAI_API_KEY}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'gpt-4',
                        'messages': [{'role': 'user', 'content': full_prompt}]
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
            question, interaction, is_dm = question_queue.popleft()  # Get the oldest question from the queue
            gpt_response = await ask_openai(question)  # Send the question to ChatGPT

            # Check if the question was from a DM or a text channel
            if is_dm:
                # Respond in DM
                await interaction.channel.send(f"Your ChatGPT response: {gpt_response}")
            else:
                # Respond in the text channel
                await interaction.channel.send(f"{interaction.user.display_name}'s ChatGPT response: {gpt_response}")
        
        await asyncio.sleep(1)  # Check the queue every 1 second

# Remove automatic DM processing
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return  # Ignore messages from the bot itself

    # We no longer automatically respond to direct messages
    await bot.process_commands(message)  # Process only commands

# /say command that adds a question to the queue from text channels
@bot.tree.command(name="say")
async def say(interaction: discord.Interaction, *, message: str):
    # Respond immediately with "Processing..." to complete the interaction then delete message to clean text channel
    await interaction.response.send_message("Processing...", delete_after=5)

    # Add the question and interaction object to the queue (False to indicate it's from a text channel)
    question_queue.append((message, interaction, False))

# /sayiac command that extracts text from an image (from DMs or lecture channel)
@bot.tree.command(name="sayiac")
async def sayiac(interaction: discord.Interaction, *, message: str):
    # Respond immediately with "Processing..." to end the interaction quickly then delete message to clean text channel
    await interaction.response.send_message("Processing your image and question...", delete_after=5)

    # Check if the command was sent in a DM or in a server text channel
    if interaction.guild is None:
        # The command was sent from a DM, so look for the most recent image in this DM
        asyncio.create_task(process_image_from_dm(interaction, message))
    else:
        # The command was sent from a text channel, process image from "lecture" channel
        asyncio.create_task(process_image_from_lecture(interaction, message))

# Background task to process the image in the DM
async def process_image_from_dm(interaction: discord.Interaction, user_question: str):
    # Fetch the most recent message with an image in the DM
    image_message = None
    async for msg in interaction.channel.history(limit=50):
        if msg.attachments:
            for attachment in msg.attachments:
                if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_message = msg
                    break
        if image_message:
            break

    if not image_message:
        await interaction.channel.send("No image found in your recent direct messages. Please send an image and try again.")
        return

    # Download the image and extract text using pytesseract
    image_data = await image_message.attachments[0].read()
    image = Image.open(io.BytesIO(image_data))
    extracted_text = pytesseract.image_to_string(image)

    # Construct the prompt to send to ChatGPT
    constructed_prompt = f'ImageAsText: "{extracted_text}". UserQuestion: "{user_question}".'

    # Add the constructed prompt and interaction object to the queue
    question_queue.append((constructed_prompt, interaction, True))

# Background task to process the image in the "lecture" channel
async def process_image_from_lecture(interaction: discord.Interaction, user_question: str):
    # Fetch the "lecture" channel by name
    lecture_channel = discord.utils.get(interaction.guild.text_channels, name="lecture")
    if not lecture_channel:
        await interaction.channel.send("Lecture channel not found!")
        return

    # Fetch the most recent message with an image in the "lecture" channel
    image_message = None
    async for msg in lecture_channel.history(limit=50):
        if msg.attachments:
            for attachment in msg.attachments:
                if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_message = msg
                    break
        if image_message:
            break

    if not image_message:
        await interaction.channel.send("No image found in the recent messages.")
        return

    # Download and process the image
    image_data = await image_message.attachments[0].read()
    image = Image.open(io.BytesIO(image_data))
    extracted_text = pytesseract.image_to_string(image)

    # Construct the prompt to send to ChatGPT
    constructed_prompt = f'ImageAsText: "{extracted_text}". UserQuestion: "{user_question}".'

    # Add the constructed prompt and interaction object to the queue
    question_queue.append((constructed_prompt, interaction, False))

# Start the background task when the bot is ready
@bot.event
async def on_ready():
    bot.loop.create_task(process_queue())  # Start the queue processor
    await bot.tree.sync()  # Sync commands to ensure they're registered with Discord
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