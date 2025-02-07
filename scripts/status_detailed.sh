#!/bin/bash

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Check the status of the labelbot service with detailed logs
if sudo journalctl -u labelbot.service -n 10 -f; then
  echo "Service status retrieved successfully."
else
  echo "Failed to retrieve the service status."
  exit 1
fi