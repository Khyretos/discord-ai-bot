# OpenWebUI-Discordbot

A Discord bot that interfaces with an OpenWebUI instance to provide AI-powered responses in your Discord server.

## Prerequisites

- Docker (for containerized deployment)
- Python 3.8 or higher+ (for local development)
- A Discord Bot Token ([How to create a Discord Bot Token](https://www.writebots.com/discord-bot-token/))
- Access to an OpenWebUI instance

## Installation

##### Running locally

1. Clone the repository
2. Copy `.env.sample` to `.env` and configure your environment variables:

```env
DISCORD_TOKEN=your_discord_bot_token
OPENWEBUI_API_KEY=your_openwebui_api_key
OPENWEBUI_API_BASE=http://your_openwebui_instance:port/api
MODEL_NAME=your_model_name
```

3. Build and run the bot using the following commands:

```sh
# Install dependencies
pip install --no-cache-dir discord.py python-dotenv requests asyncio

# Run the bot
python bot.py
```

##### Running via Docker

1. Clone the repository
2. Copy `.env.sample` to `.env` and configure your environment variables as described above.
3. Build and run the bot using Docker Compose:

```sh
docker-compose up --build
```

##### Docker Compose Example (`docker-compose.yml`)

```yaml
version: "3"

services:
  discord-ai-bot:
  container-name: discord-ai-bot
  restart: unless-stopped
  build: .
  volumes:
    - ./app:/app
  env_file:
    - .env
```
