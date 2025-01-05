#!/bin/sh

# Stop the service for 30 minutes then start it again

sudo systemctl stop labelbot.service
echo "Service stopped for 30 minutes."

# Wait for 30 minutes (1800 seconds)
sleep 1800

sudo systemctl start labelbot.service
echo "Service started after 30 minutes. successfully."