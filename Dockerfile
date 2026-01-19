# Use Python 3 base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio support
RUN apt-get update && apt-get install -y \
    python3-pip \
    libopus0 \
    && rm -rf /var/lib/apt/lists/*

# Install required packages
RUN pip install --no-cache-dir discord.py python-dotenv requests asyncio

# Copy the bot script
COPY /scripts/bot.py /app

# Copy the env files
COPY ./env /app

# Run the bot on container start
CMD ["python", "bot.py"]