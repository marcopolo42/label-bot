#!/bin/bash

# Navigate to the project directory
cd /home/orangepi/label-bot || exit

# File paths
REQUIREMENTS_FILE="requirements.txt"

# Compute checksum before Git pull
PRE_PULL_CHECKSUM=$(md5sum $REQUIREMENTS_FILE | awk '{print $1}' 2>/dev/null)

# Pull the latest changes from the main branch
git pull origin main

# Compute checksum after Git pull
POST_PULL_CHECKSUM=$(md5sum $REQUIREMENTS_FILE | awk '{print $1}')

# Check if the requirements.txt file has changed
if [ "$PRE_PULL_CHECKSUM" != "$POST_PULL_CHECKSUM" ]; then
    echo "Detected changes in $REQUIREMENTS_FILE. Installing requirements..."

    # Install updated requirements
    sudo .venv/bin/pip3 install -r $REQUIREMENTS_FILE

    echo "Requirements updated successfully."
else
    echo "No changes detected in $REQUIREMENTS_FILE. Skipping requirements installation."
fi

# Restart the service
sudo systemctl restart labelbot.service

echo "Project updated and service restarted successfully."