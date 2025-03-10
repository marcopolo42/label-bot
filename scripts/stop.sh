#!/bin/bash

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Stop the labelbot service
if sudo systemctl stop labelbot.service; then
  echo "Service stopped successfully."
else
  echo "Failed to stop the service."
  exit 1
fi