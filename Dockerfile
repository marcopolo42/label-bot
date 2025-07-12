# Base image
FROM python:3.11-slim

# Metadata
LABEL maintainer="Marco_polo"
LABEL description="Label Bot is a python discord bot used to print stickers using a brother ql printer."

# Set working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    screen \
    cups \
    libpango1.0-0 \
    fonts-dejavu \
    fonts-liberation \
    fonts-freefont-ttf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /app

#install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Define entrypoint to run the bot
ENTRYPOINT ["python", "bot.py"]
