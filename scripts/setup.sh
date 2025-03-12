#!/bin/bash

# Setup of the label-bot working environment
cd /home/admin/label-bot || { echo "Directory /home/admin/label-bot not found"; exit 1; }

# Update package list
apt-get update

# Install necessary fonts
apt-get install -y fonts-dejavu fonts-liberation fonts-freefont-ttf

# Install necessary packages
apt-get install -y vim git python3-full python3-pip screen libpangocairo-1.0-0

# Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip3 install -r requirements.txt

# Create a systemd service
cp labelbot.service /etc/systemd/system/
systemctl enable labelbot.service

echo "Setup completed successfully."