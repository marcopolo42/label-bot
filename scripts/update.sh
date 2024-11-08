#!/bin/bash

# Navigate to the project directory
cd /home/admin/label-bot || exit

# Pull the latest changes from the main branch
git pull origin main

# Restart the service (replace 'your-service' with the actual service name)
sudo systemctl restart labelbot.service

echo "Project updated and service restarted successfully."