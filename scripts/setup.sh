#!/bin/bash

# setup of the label-bot working environment
cd /home/admin/label-bot || exit

sudo apt update
#necessary fonts
sudo apt install fonts-dejavu fonts-liberation fonts-freefont-ttf
#necessary packages
sudo apt install -y vim git python3-full python3-pip screen libpangocairo-1.0-0
python3 -m venv .venv
source .venv/bin/activate
sudo .venv/bin/pip3 install -r requirements.txt

# Create a systemd service
cp labelbot.service /etc/systemd/system/
sudo systemctl enable labelbot.service

echo "Setup completed successfully."
