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
