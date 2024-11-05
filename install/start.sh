#!/bin/sh

# Create a systemd service
cp labelbot.service /etc/systemd/system/
sudo systemctl enable labelbot.service
sudo systemctl start labelbot.service