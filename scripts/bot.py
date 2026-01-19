import os
import json
import base64
from io import BytesIO
import logging
import discord
from discord.ext import commands
from discord import app_commands
import requests
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Get environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")
OPENWEBUI_API_BASE = os.getenv("OPENWEBUI_API_BASE")
MODEL_NAME = os.getenv("MODEL_NAME")

# Initialize logger
logger = logging.getLogger("discord.gateway")
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("aiohttp.client").setLevel(logging.ERROR)


# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Message history cache
channel_history = {}


async def chat_request(prompt):
    """Function that sends the request to generate a chat response"""
    headers = {
        "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
        "Content-Type": "application/json",
    }

    # body = json.dumps(
    #     {
    #         "stream": False,
    #         "model": MODEL_NAME,
    #         "messages": [{"role": "user", "content": prompt}],
    #         "features": {
    #             "image_generation": False,
    #             "code_interpreter": False,
    #             "web_search": True,
    #         },
    #         "background_tasks": {"title_generation": True},
    #     }
    # )

    body = json.dumps(
        {
            "chat_id": "4a299940-11b4-49e7-9844-5c39e2a2955c",
            "stream": False,
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "features": {
                "image_generation": False,
                "code_interpreter": False,
                "voice": False,
                "web_search": True,
            },
            "background_tasks": {"title_generation": True},
        }
    )

    response = requests.post(
        OPENWEBUI_API_BASE + "/api/chat/completions",
        data=body,
        headers=headers,
        timeout=600,
    )

    # Convert the body to JSON format
    return response


async def generate_chat_response(prompt):
    """Function that starts the process of generating a chat response"""

    response = await chat_request(prompt)
    embed = discord.Embed()

    if response.status_code != 200:
        embed.title(f"Request failed with status code {response.status_code}")
        print(embed.title)
        embed.description("Error message:", response.text)
        print(embed.description)
        embed.color = 0xFF0000
        return embed

    embed.add_field(name="Question", value=prompt, inline=False)

    # Convert json into dictionary
    response_dict = response.json()

    # Print response in console (just in case)
    print(json.dumps(response_dict, indent=4))

    # Default values
    title = "Answer"
    embed.color = 0xFF0000

    # Check if "sources" exists and is valid
    if "sources" in response_dict and response_dict["sources"]:
        try:
            title = response_dict["sources"][0]["source"]["name"]
            embed.color = 0x00AEEF
        except (KeyError, IndexError, TypeError):
            pass  # Keep defaults if nested fields are missing

    # Always set the embed fields safely
    try:
        embed.title = title
        embed.description = response_dict["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        embed.title = "Error in parsing the response"
        embed.description = "Check the logs"
        embed.color = 0xFF0000
        return embed

    try:
        # Parse the response and get the metadata (the sources of the generated awnser)
        metadata = response_dict["sources"][0]["metadata"]
        formatted_sources = "\n".join(
            [
                f"[{item['title']}]({item['source']})"
                for item in metadata
                if "title" in item and "source" in item
            ]
        )
        if formatted_sources:
            embed.add_field(name="Sources", value=formatted_sources, inline=False)
    except (KeyError, IndexError, TypeError):
        # No need to get the error message of metadata since it is not always filled.
        pass

    return embed


async def download_image(download_endpoint):
    """Function that sends the request to download the generated image"""

    headers = {
        "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
        "Content-Type": "image/png",
    }

    response = requests.get(
        OPENWEBUI_API_BASE + download_endpoint, headers=headers, timeout=60
    )

    if response.status_code != 200:
        print(f"Request failed with status code {response.status_code}")
        print("Error message:", response.text)
        return None

    image_data = BytesIO(response.content)
    base64_image = base64.b64encode(image_data.read()).decode("utf-8")
    return base64_image


async def image_request(prompt):
    """Function that sends the request to generate a image response"""

    headers = {
        "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
        "Content-Type": "application/json",
    }

    body = json.dumps(
        {
            "model": "dreamshaper_8",
            "prompt": prompt,
        }
    )

    response = requests.post(
        OPENWEBUI_API_BASE + "/api/v1/images/generations",
        data=body,
        headers=headers,
        timeout=600,
    )

    return response


async def generate_image_response(prompt):
    """Function that starts the process of generating a image response"""

    response = await image_request(prompt)

    embed = discord.Embed()

    if response.status_code != 200:
        embed.title = f"Request failed with status code {response.status_code}"
        print(embed.title)
        embed.description = "Error message:", response.text
        print(embed.description)
        return embed

    response_dict = response.json()

    print(json.dumps(response_dict, indent=4))

    # Parse image URL correctly
    try:
        download_endpoint = response_dict[0]["url"]
    except (KeyError, IndexError, TypeError):
        embed.title = "Error in parsing the response"
        embed.description = "Check the logs"
        embed.color = 0xFF0000
        return embed, None

    base64_image = await download_image(download_endpoint)

    if base64_image is None:
        embed.title = "Error in downloading the image"
        embed.description = "Check the logs"
        embed.color = 0xFF0000
        return embed, None

    embed.title = "Generated image"
    embed.description = prompt

    img_bytes = BytesIO(base64.b64decode(base64_image))
    img_file = discord.File(img_bytes, filename="image.png")
    embed.set_image(url="attachment://image.png")

    return embed, img_file


# IMAGE COMMAND
# @bot.tree.command(name="image", description="Generate an image from a prompt")
# @app_commands.describe(prompt="What image do you want?")
# async def image_cmd(interaction: discord.Interaction, prompt: str):
#     """The command that is used to generate a image response based on a question"""
#     await interaction.response.defer()

#     reply, img_file = await generate_image_response(prompt)

#     await interaction.followup.send(embed=reply, file=img_file)


# QUESTION COMMAND
@bot.tree.command(name="question", description="Ask a question and get a text reply")
@app_commands.describe(prompt="What is your question?")
async def question_cmd(interaction: discord.Interaction, prompt: str):
    """The command that is used to generate a text response based on a question"""
    await interaction.response.defer()

    reply = await generate_chat_response(prompt)

    await interaction.followup.send(embed=reply)


async def get_chat_history(channel, limit=100):
    """Function that triggers when a conversation is started with the bot, it will get the chat history to have more context to work with"""
    messages = []
    async for message in channel.history(limit=limit):
        content = f"{message.author.name}: {message.content}"

        # Handle attachments (images)
        for attachment in message.attachments:
            if any(
                attachment.filename.lower().endswith(ext)
                for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
            ):
                content += f" [Image: {attachment.url}]"

        messages.append(content)
    return "\n".join(reversed(messages))


@bot.event
async def on_message(message):
    """Function that triggers when a message has been received"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    should_respond = False

    # Check if bot was mentioned
    if bot.user in message.mentions:
        should_respond = True

    # Check if message is a DM
    if isinstance(message.channel, discord.DMChannel):
        should_respond = True

    if should_respond:
        async with message.channel.typing():
            # Get chat history
            history = await get_chat_history(message.channel)

            # Remove bot mention from the message
            user_message = message.content.replace(f"<@{bot.user.id}>", "").strip()

            # Collect image URLs from the message
            image_urls = []
            for attachment in message.attachments:
                if any(
                    attachment.filename.lower().endswith(ext)
                    for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
                ):
                    image_urls.append(attachment.url)

            # Get AI response
            response = await generate_chat_response(user_message)

            # Send response
            await message.reply(embed=response)

    await bot.process_commands(message)


@bot.event
async def on_ready():
    """Function that runs when the bot is ready to be used"""
    synced = await bot.tree.sync()
    print(f"Slash commands synced to guild. Commands: {len(synced)}")
    print(f"Logged in as {bot.user}")


@bot.event
async def on_disconnect():
    """Function that triggers when the on_disconnect event is triggered."""
    logger.warning("Bot disconnected from Discord. Attempting to reconnect...")


@bot.event
async def on_resumed():
    """Function that triggers when the on_resumed event is triggered."""
    logger.info("Bot connection resumed.")


def main():
    """Main process to initialize the AI bot."""
    if not all([DISCORD_TOKEN, OPENWEBUI_API_KEY, OPENWEBUI_API_BASE, MODEL_NAME]):
        print("Error: Missing required environment variables")
        return

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
