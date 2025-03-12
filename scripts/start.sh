#!/bin/bash

# Start the labelbot service
if sudo systemctl start labelbot.service; then
  echo "Service started successfully."
else
  echo "Failed to start the service."
  exit 1
fi