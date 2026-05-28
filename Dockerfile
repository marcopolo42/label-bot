# Base image
FROM python:3.11-slim

# Metadata
LABEL maintainer="Marco_polo"
LABEL description="Label Bot is a python discord bot used to print stickers using a brother ql printer."

# Set working directory
WORKDIR /app

# System dependencies (including build tools for Pillow and other C extensions)
RUN apt-get update && apt-get install -y \
    git \
    vim \
    screen \
    cups \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    fonts-dejavu \
    fonts-liberation \
    fonts-freefont-ttf \
    fonts-noto-color-emoji \
    libjpeg-dev \
    libtiff-dev \
    libffi-dev \
    zlib1g-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /app

# Remove any host-generated build artifacts to avoid packaging metadata leaking into the image
RUN rm -rf /app/*.egg-info /app/build /app/dist || true

# Install build tool
RUN pip install --upgrade pip build

# Build the wheel and install it into the system environment
RUN python3 -m build --wheel && \
    python3 -m pip install dist/*.whl

# Define entrypoint to run the bot directly
ENTRYPOINT ["labelbot"]