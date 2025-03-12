#!/bin/bash

# Check the status of the labelbot service
if sudo systemctl status -f labelbot.service; then
  echo "Service status retrieved successfully."
else
  echo "Failed to retrieve the service status."
  exit 1
fi