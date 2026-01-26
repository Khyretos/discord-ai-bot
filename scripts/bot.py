"""
This file contains the implementation of a Discord bot that can generate text and images based on user input using OpenWebUI API.
The bot has commands to ask questions, get the name of the currently loaded language model, and generate images based on prompts.
The bot's functionality is provided through a Discord bot using the discord and discord.app_commands libraries.
The bot fetches chat history, removes mentions and bot messages, and sends responses based on user commands.
The responses can be text or images, depending on the user's input and the bot's configuration.
The bot also handles events such as ready, disconnect, and resume to maintain its connection and respond to user messages.
The implementation utilizes classes, methods, and tools to handle text and image processing, including the chat request and response functions.
Error handling and logging are implemented to ensure efficient and reliable operation of the bot.
"""

import base64
import json
import logging
import os
import re
from io import BytesIO

import aiohttp
import discord
import requests
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from pagination import Pagination

# Load environment variables
load_dotenv()

# Get environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")
OPENWEBUI_API_BASE = os.getenv("OPENWEBUI_API_BASE")
MODEL_NAME = os.getenv("MODEL_NAME")

# Initialize logger
# TODO: define more logging types
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


@bot.command(name="update")
@commands.is_owner()  # Restrict to bot owner to prevent misuse
async def sync(ctx: commands.Context):
    """Sync application commands globally."""
    await ctx.bot.tree.sync()
    await ctx.send("Application commands synchronized!")


def is_empty_or_null(string) -> bool:
    """
    Checks if the provided string is either None or an empty string.

    Args:
        string (str): The string to check.

    Returns:
        bool: True if the string is None or empty, False otherwise.
    """
    if string is None or string == "":
        return True
    return False


@bot.tree.command(name="test_message", description="worst case scenario test message")
async def show(interaction: discord.Interaction):
    """
    Responds to a user interaction with the worst case scenario type of message
    """
    await interaction.response.defer()
    think_list = split_string_into_chunks(
        "<think>\r\nOkay, the user is asking why I can't explain Warframe's mechanics and data well. Let me start by understanding their situation. They might be a player encountering issues, maybe a new or returning player struggling with game mechanics. Their frustration could stem from not finding clear explanations, affecting their gameplay experience.\r\n\r\nFirst, I need to acknowledge their frustration. It's important to validate their feelings. Then, explain the limitations: Warframe's complexity and my AI constraints. The game has vast content with constant updates, making it hard to keep up. Also, Warframe's unique mechanics, like the Void, Warframes, and weapons, are interconnected in ways that require deep gameplay understanding, which I don't have firsthand.\r\n\r\nI should break down the reasons clearly. Mention the game's scale, the dynamic nature of updates, and the lack of official data. Highlight that my knowledge is based on community sources, which can be outdated. Emphasize that I can't access real-time data or the game's backend.\r\n\r\nNext, offer solutions. Suggest specific resources like the official wiki, forums, and guides. Provide examples of how to navigate those resources. Also, ask them to specify what they're struggling with so I can give targeted advice. Maybe they need help with a particular mechanic, like Void traversal or weapon builds. Tailoring the response to their specific question would be more helpful.\r\n\r\nCheck if there's an unspoken need. They might be looking for a way to improve their gameplay or troubleshoot a bug. They could be new and overwhelmed, or a veteran needing help with a new update. Understanding their exact issue would help provide a better answer. Encourage them to share details so I can assist more effectively.\r\n\r\nFinally, reassure them that while I can't replace in-game guides, I can help point them to the right resources. Offer to summarize key points or help them interpret existing guides. Make sure the tone is supportive and encouraging, showing willingness to help them succeed in Warframe.</think>",
        1024,
    )
    awnser_list = split_string_into_chunks(
        '\r\n\r\nEntiendo tu frustraci\u00f3n. Warframe es un juego extremadamente complejo y din\u00e1mico, y explicar sus mec\u00e1nicas y datos con precisi\u00f3n requiere una profundidad de conocimiento que yo, como modelo de lenguaje, no poseo de forma directa. Aqu\u00ed explico las razones y c\u00f3mo puedo ayudarte mejor:\r\n\r\n**\u00bfPor qu\u00e9 no puedo explicar bien mec\u00e1nicas/datos de Warframe?**\r\n\r\n1.  **La Escala y la Complejidad:** Warframe tiene una base de conocimiento *inmensa*. Incluye:\r\n    *   **M\u00faltiples sistemas interconectados:** Void (traves\u00eda, recursos, misiones), Warframes (cada uno con habilidades \u00fanicas), Armas (categor\u00edas, modos, bal\u00edstica), Modificadores (modos de combate, habilidades), Misiones (deportes, misiones secundarias, misiones del Void), Cultivos, Fabricaci\u00f3n, etc.\r\n    *   **Constante actualizaci\u00f3n:** El juego evoluciona constantemente con nuevos Warframes, Armas, Misiones, Modificadores y ajustes mec\u00e1nicos. Lo que escribo hoy podr\u00eda ya estar obsoleto ma\u00f1ana.\r\n    *   **Interdependencia:** Mec\u00e1nicas no funcionan de forma aislada. Por ejemplo, la eficacia de un Warframe depende de su habilidad, el modo de combate activo, el tipo de arma, y hasta el estado del Void en el que se combate.\r\n\r\n2.  **Limitaciones de mi conocimiento:** No tengo acceso directo al c\u00f3digo fuente del juego, a bases de datos en tiempo real, ni a las actualizaciones de desarrolladores. Mi conocimiento se basa en:\r\n    *   **Informaci\u00f3n publicada oficialmente:** Sitio web de Warframe, Warframe Wiki (actualizado por la comunidad), Discord y Discord Bot, Twitter de Warframe, etc.\r\n    *   **Contenido de la comunidad:** Foros (Reddit, Warframe Forums), videos (YouTube, Twitch), gu\u00edas y an\u00e1lisis de jugadores expertos.\r\n    *   **Mi propia experiencia:** Algunos usuarios me comparten sus propias experiencias, pero esto puede ser subjetivo y no siempre representativo.\r\n\r\n3.  **Riesgo de inexactitud:** Dado que mi conocimiento proviene de m\u00faltiples fuentes y se actualiza a trav\u00e9s de entrenamiento (sin actualizaciones en tiempo real), es posible que:\r\n    *   **Los datos sean obsoletos:** Un dato que escribo hoy podr\u00eda ya estar desactualizado tras una actualizaci\u00f3n.\r\n    *   **Los detalles est\u00e9n incompletos o incorrectos:** Especialmente para mec\u00e1nicas complejas o nuevas, donde la comunidad a\u00fan est\u00e1 analizando.\r\n    *   **Fallos en la comprensi\u00f3n:** Algunas mec\u00e1nicas son tan abstractas o interdependientemente complejas que pueden ser malinterpretadas o explicadas de manera inexacta.\r\n\r\n**\u00bfC\u00f3mo puedo ayudarte mejor con Warframe?**\r\n\r\nAunque no puedo "saber" mec\u00e1nicas y datos con la precisi\u00f3n de un jugador experimentado, puedo ofrecerte recursos y estrategias:\r\n\r\n1.  **Dirige a recursos oficiales y comunitarios:**\r\n    *   **Warframe Wiki (oficial):** [https://warframe.wikia.com/wiki/Warframe_Wiki](https://warframe.wikia.com/wiki/Warframe_Wiki) - Es el principal recurso oficial, actualizado por jugadores y moderadores. Contiene informaci\u00f3n detallada sobre Warframes, Armas, Misiones, Modificadores, etc.\r\n    *   **Warframe Forums:** [https://forums.warframe.com/](https://forums.warframe.com/) - \u00datil para discusiones t\u00e9cnicas, bugs reportados por jugadores, y discusiones comunitarias.\r\n    *   **Discord de Warframe:** [https://discord.gg/3pJ9p6Q](https://discord.gg/3pJ9p6Q) - Comunidad activa con jugadores que responden preguntas.\r\n    *   **YouTube/Twitch:** Canales dedicados (como `WarframeGuides`, `WarframeDPS`, `WarframeExplained`) ofrecen gu\u00edas visuales detalladas para mec\u00e1nicas espec\u00edficas.\r\n\r\n2.  **Preguntas espec\u00edficas:** Cu\u00e9ntame *exactamente* qu\u00e9 mec\u00e1nica, dato o situaci\u00f3n te est\u00e1 causando dificultad. Por ejemplo:\r\n    *   "\u00bfC\u00f3mo funciona exactamente la habilidad de *Warframe X*?"\r\n    *   "\u00bfQu\u00e9 significa que un *Modificador* es \'de tipo *Y*\' y c\u00f3mo afecta a los Warframes?"\r\n    *   "\u00bfPor qu\u00e9 mi *Arma Z* se destruye tan r\u00e1pido en el Void?"\r\n    *   "\u00bfQu\u00e9 Warframe es el mejor para *Misi\u00f3n del Void A*?"\r\n    *   "\u00bfQu\u00e9 significa el c\u00f3digo de error *XYZ*?"\r\n    *   "\u00bfC\u00f3mo calculo el da\u00f1o de un *Modificador* en combate?"\r\n    *   "\u00bfPor qu\u00e9 mi *Void Run* no se est\u00e1 completando? (Detalla el problema)"\r\n\r\n3.  **An\u00e1lisis basado en lo que sabes:** Si me proporcionas detalles espec\u00edficos (ej. el nombre del Warframe, el Modificador, el tipo de arma, el Void, el modo de combate, etc.), puedo:\r\n    *   **Explicar el concepto general:** Dando una descripci\u00f3n te\u00f3rica de *c\u00f3mo deber\u00eda* funcionar seg\u00fan lo que entiendo de la mec\u00e1nica.\r\n    *   **Sugerir posibles causas:** Bas\u00e1ndome en mi conocimiento de mec\u00e1nicas similares o comunidades, proponer razones *probables* por las que algo podr\u00eda estar sucediendo (ej: "Podr\u00eda ser que el *Modificador* *X* est\u00e9 activo y est\u00e9 restringiendo la habilidad", "Es posible que el *Void* est\u00e9 muy alto y est\u00e9 afectando la eficiencia de los recursos").\r\n    *   **Dirigirte a recursos:** Recomiendo espec\u00edficamente art\u00edculos de la Wiki o gu\u00edas comunitarias que aborden el tema.\r\n    *   **Aconsejar m\u00e9todos de diagn\u00f3stico:** Ej: "Prueba desactivar todos los modificadores de habilidad y ver si el problema persiste".\r\n\r\n**Ejemplo de c\u00f3mo puedo ayudarte:**\r\n\r\n*   **Tu pregunta:** "\u00bfPor qu\u00e9 mi Warframe *Tesla* se destruye tan r\u00e1pido en el Void?"\r\n*   **Mi respuesta:**\r\n    *   **Explicaci\u00f3n general:** "El Warframe Tesla es un Warframe de tipo *Void* (mejor para combates en el Void). Sin embargo, su habilidad principal (*Tesla*) es un *Modificador de da\u00f1o* que aumenta el da\u00f1o de todos los ataques. Esto puede ser peligroso si est\u00e1s usando Armas que ya generan mucho da\u00f1o, o si est\u00e1s en un Void muy alto donde los da\u00f1os se multiplican."\r\n    *   **Sugerir causas:** "Podr\u00edas estar usando un *Modificador de Da\u00f1o* (como *Overload* o *Void Overload*) que est\u00e9 combinado con la habilidad Tesla, lo que podr\u00eda multiplicar el da\u00f1o excesivamente. Tambi\u00e9n es posible que est\u00e9s usando un *Modificador de Estilo* (como *Soul* o *Void Soul*) que est\u00e9 aumentando tu da\u00f1o de base, lo que tambi\u00e9n se ver\u00eda amplificado por Tesla."\r\n    *   **Dirigir a recursos:** "Revisa la p\u00e1gina de Tesla en la [Wiki](https://warframe.wikia.com/wiki/Tesla) para ver c\u00f3mo interact\u00faan sus habilidades con los Modificadores. En la [Wiki](https://warframe.wikia.com/wiki/Modifiers), busca c\u00f3mo los Modificadores de Da\u00f1o y de Estilo afectan a los Warframes."\r\n    *   **Sugerencia de diagn\u00f3stico:** "Prueba desactivar cualquier *Modificador de Da\u00f1o* o *Modificador de Estilo* que est\u00e9s usando. Si el problema persiste, prueba un Warframe sin habilidades de da\u00f1o o con habilidades neutrales para ver si el problema desaparece."\r\n\r\n**Conclusi\u00f3n:** No puedo "saber" Warframe como un jugador, pero puedo ser un puente hacia la informaci\u00f3n disponible. Tu colaboraci\u00f3n es clave: cuanto m\u00e1s espec\u00edfico sea tu pregunta, m\u00e1s \u00fatil puedo ser, incluso si solo puedo apuntar a recursos o proponer hip\u00f3tesis basadas en mi conocimiento limitado. La comunidad y los recursos oficiales siguen siendo los m\u00e1s confiables.',
        4096,
    )
    await show_generated_awnser(
        interaction,
        "a title",
        awnser_list,
        think_list,
        "the source list",
        "the question",
    )


def find_highest(numbers: int) -> int:
    """
    Finds the highest number in a given list of integers.

    Parameters:
    numbers (List[int]): A list of integers.

    Returns:
    int: The highest number in the list.
    """
    if not numbers:
        return 1
    return max(numbers)


def part_string(current_part: int, amount_of_parts: int) -> str:
    """
    Generate a string indicating the current part number and total number of parts.

    Args:
        current_part (int): The current part number (1-based index).
        amount_of_parts (int): The total number of parts.

    Returns:
        str: A string indicating the current part number and total number of parts, or an empty string if there is only one part.
    """
    if amount_of_parts == 1:
        return ""
    return f" (Part {current_part} of {amount_of_parts})"


async def show_generated_awnser(
    interaction: discord.Interaction,
    title: str,
    awnser_list: list[str],
    think_list: list[str],
    formatted_sources: str,
    prompt: str,
):
    """
    Generates and shows a paginated response to an interaction with a list of answers and their corresponding thoughts.

    Args:
        interaction (discord.Interaction): The interaction to respond to.
        title (str): The title of the response embed.
        awnser_list (list[str]): The list of generated answers.
        think_list (list[str]): The list of thoughts or explanations for each answer.
        formatted_sources (str): The formatted sources or references for the answers.
        prompt (str): The original prompt or question that generated the answers.

    Returns:
        None
    """

    async def get_page(page: int):
        """
        Generates a page of the response embed for the given page number.

        Args:
            page (int): The page number to generate.

        Returns:
            tuple: A tuple containing the generated embed (discord.Embed) and the total number of pages (int).
        """
        emb = discord.Embed(title=title, description="")
        amount_of_pages: int = find_highest([len(awnser_list), len(think_list)])
        offset: int = page - 1
        if offset <= len(awnser_list):
            for awnser in awnser_list[offset : offset + 1]:
                emb.description += f"{awnser}\n"
        if len(think_list) > 0 and offset <= len(think_list):
            for thought in think_list[offset : offset + 1]:
                current_part_string: str = part_string(offset + 1, amount_of_pages)
                emb.add_field(
                    name=f"Thought process {current_part_string}",
                    value=f"{thought}\n",
                    inline=False,
                )
        n = Pagination.compute_total_pages(amount_of_pages, 1)

        emb.add_field(name="Question", value=prompt, inline=False)

        emb.add_field(name="Sources", value=f"{formatted_sources}", inline=False)

        if n > 1:
            emb.set_footer(text=f"Page {page} from {n}")

        return emb, n

    await Pagination(interaction, get_page, generate_chat_response, logger).navegate()


def split_string_into_chunks(input_string: str, max_chunk_size: int) -> list[str]:
    """
    Splits a string into chunks of specified size.

    Args:
        input_string (str): The string to be split.
        max_chunk_size (int): The maximum size of each chunk.

    Returns:
        list[str]: A list of chunks of the input string.
    """
    chunks = []
    for i in range(0, len(input_string), max_chunk_size):
        chunks.append(input_string[i : i + max_chunk_size])
    return chunks


def extract_thought_and_awnser(input_string):
    """
    Extracts all occurrences of text within <think>...</think> tags and the remaining text from the input string.

    Args:
        input_string (str): The input string containing text with <think>...</think> tags.

    Returns:
        list of tuples: A list where each tuple contains two elements:
            - The extracted text within <think>...</think> tags.
            - The remaining text from the input string with the <think>...</think> tags removed.
    """
    pattern = r"<think>(.*?)</think>"
    thoughts = re.findall(pattern, input_string, re.DOTALL)

    if len(thoughts) == 0:
        thoughts = [""]

    awnser = re.sub(pattern, "", input_string).strip()
    result = [awnser, thoughts[0]]

    return result


async def chat_request(prompt: str) -> list[str]:
    """
    Sends a chat request to the OpenWebUI API with the given prompt.

    Args:
        prompt (str): The user's prompt for the chat request.

    Returns:
        response (Response): The response from the OpenWebUI API.
    """
    response: aiohttp.ClientResponse = None

    headers = {
        "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
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

    url: str = OPENWEBUI_API_BASE + "/api/chat/completions"
    timeout = aiohttp.ClientTimeout(total=600)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=body, headers=headers) as response:
            logger.info(f"Status: {response.status}")
            if not response.status == 200:
                logger.info(f"Failed to get response, Error message: {response}")
                return None
            response_data = await response.json()
            logger.info(f"Resonse body: {response}")
            return response_data


async def generate_chat_response(interaction: discord.Interaction, prompt):
    """
    Generates a chat response based on the given prompt.

    Args:
        interaction (discord.Interaction): The interaction object.
        prompt (str): The prompt for the chat response.

    Returns:
        discord.Embed: The embed object containing the chat response.
    """

    await interaction.response.defer()

    print(f"original response: {interaction.original_response}")

    response: json = await chat_request(prompt)
    embed = discord.Embed(title="test", description="")

    thought_list: list[str] = []
    awnser_list: list[str] = []
    formatted_sources: str = ""

    # embed.title("Request failed with status code ")

    if not response:
        embed.title = "Failed to get response"
        embed.color = 0xFF0000
        await interaction.response.edit_original_response(embed=embed)

    # Print response in console (just in case)
    logger.info(json.dumps(response, indent=4))
    # Default values
    title = "Answer"
    embed.color = 0xFF0000

    # Check if "sources" exists and is valid
    if "sources" in response and response["sources"]:
        try:
            title = response["sources"][0]["source"]["name"][:256]
            embed.color = 0x00AEEF
        except (KeyError, IndexError, TypeError):
            pass  # Keep defaults if nested fields are missing

    # Always set the embed fields safely
    try:
        result: list[str] = extract_thought_and_awnser(
            response["choices"][0]["message"]["content"]
        )

        if not is_empty_or_null(result[1]):
            thought_list = split_string_into_chunks(result[1], 1024)

        if not is_empty_or_null(result[0]):
            awnser_list = split_string_into_chunks(result[0], 4096)

    except (KeyError, IndexError, TypeError):
        embed.title = "Error in parsing the response"
        embed.description = "Check the logs"
        embed.color = 0xFF0000
        await interaction.response.send_message(embed=embed)

    try:
        # Parse the response and get the metadata (the sources of the generated awnser)
        metadata = response["sources"][0]["metadata"]
        formatted_sources = "\n".join(
            [
                f"[{item['title']}]({item['source']})"
                for item in metadata
                if "title" in item and "source" in item
            ]
        )

    except (KeyError, IndexError, TypeError):
        # No need to get the error message of metadata since it is not always filled.
        pass

    await show_generated_awnser(
        interaction, title, awnser_list, thought_list, formatted_sources, prompt
    )


async def download_image(download_endpoint):
    """
    Downloads an image from the specified endpoint and returns its base64 encoded string.

    Args:
        download_endpoint (str): The endpoint URL to download the image from.

    Returns:
        str: The base64 encoded string of the downloaded image, or None if the request failed.
    """

    headers = {
        "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
        "Content-Type": "image/png",
    }

    response = requests.get(
        OPENWEBUI_API_BASE + download_endpoint, headers=headers, timeout=60
    )

    if response.status_code != 200:
        logger.error(f"Failed to get response, Error message: {response}")
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
        logger.error(f"Request failed with status code {response.status_code}")
        logger.error(f"Error message:{response.text}")
        embed.title = f"Request failed with status code {response.status_code}"
        embed.description = "Error message:", response.text
        return embed

    response_dict = response.json()

    logger.info(json.dumps(response_dict, indent=4))

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


@bot.tree.command(name="question", description="Ask a question and get a text reply")
@app_commands.describe(prompt="What is your question?")
async def question_cmd(interaction: discord.Interaction, prompt: str):
    """
    Command to generate a text response based on a user's question.

    Args:
        interaction (discord.Interaction): The interaction object representing the user's command.
        prompt (str): The question asked by the user.

    Returns:
        None
    """
    logger.info(f"Started Question command with the following prompt: {prompt}")
    await generate_chat_response(interaction, prompt)


@bot.tree.command(
    name="get_model_name", description="Returns the name of the currently loaded LLM"
)
async def model_cmd(interaction: discord.Interaction):
    """
    Returns the name of the currently loaded LLM.

    Args:
        interaction (discord.Interaction): The interaction object.

    Returns:
        None
    """
    await interaction.response.send_message(content=MODEL_NAME)


async def get_chat_history(channel, limit=100):
    """
    Fetches the chat history from a specified channel.

    Args:
        channel (discord.channel.Channel): The channel to fetch messages from.
        limit (int, optional): The number of messages to fetch. Defaults to 100.

    Returns:
        str: A string containing the chat history, with each message on a new line.
    """

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
async def on_message(message: discord.Message):
    """
    Handles incoming messages in the Discord server.

    Args:
        message (discord.Message): The message object representing the incoming message.

    Returns:
        None
    """

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
            # response = await generate_chat_response(user_message)

            # Send response
            # await message.reply(embed=response)

    await bot.process_commands(message)


@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready to receive events.
    Syncs the bot's slash commands to the guild and prints the number of commands synced.
    """
    synced = await bot.tree.sync()
    logger.info(f"Slash commands synced to guild. Commands: {len(synced)}")
    logger.info(f"Logged in as {bot.user}")


@bot.event
async def on_disconnect():
    """
    Logs a warning when the bot disconnects from Discord and attempts to reconnect.
    """
    logger.warning("Bot disconnected from Discord. Attempting to reconnect...")


@bot.event
async def on_resumed():
    """
    Event handler for when a bot's connection is resumed.
    Logs a message indicating that the connection has been resumed.
    """
    logger.info("Bot connection resumed.")


def main():
    """Main function to run the AI bot."""
    if not all([DISCORD_TOKEN, OPENWEBUI_API_KEY, OPENWEBUI_API_BASE, MODEL_NAME]):
        logger.info("Error: Missing required environment variables")
        return

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
