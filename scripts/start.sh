#!/bin/sh

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Start the labelbot service
if sudo systemctl start labelbot.service; then
  echo "Service started successfully."
else
  echo "Failed to start the service."
  exit 1
fi