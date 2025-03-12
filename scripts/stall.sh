#!/bin/bash

# Stop the service for 30 minutes then start it again
if sudo systemctl stop labelbot.service; then
  echo "Service stopped for 30 minutes."
else
  echo "Failed to stop the service."
  exit 1
fi

# Wait for 30 minutes (1800 seconds)
sleep 1800

if sudo systemctl start labelbot.service; then
  echo "Service started successfully after 30 minutes."
else
  echo "Failed to start the service."
  exit 1
fi