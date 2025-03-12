#!/bin/bash

# Stop the labelbot service
if sudo systemctl stop labelbot.service; then
  echo "Service stopped successfully."
else
  echo "Failed to stop the service."
  exit 1
fi