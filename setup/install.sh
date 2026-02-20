#!/bin/bash

# BeoSound 5 Redux - Installation Script for Raspberry Pi
set -e

echo "--- Installing System Dependencies ---"
sudo apt update
sudo apt install -y chromium-browser x11-xserver-utils xdotool unclutter xorg openbox nodejs npm python3-venv

echo "--- Setting up Backend ---"
cd /home/pi/BeoSound5redux/backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
./install_deps.sh

echo "--- Building Frontend ---"
cd /home/pi/BeoSound5redux
npm install
npm run build

echo "--- Installing Systemd Services ---"
sudo cp setup/beosound-backend.service /etc/systemd/system/
sudo cp setup/beosound-frontend.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable beosound-backend.service
sudo systemctl enable beosound-frontend.service

echo "--- Setting up Kiosk Mode ---"
chmod +x setup/kiosk.sh

# Setup Openbox to use our kiosk script
mkdir -p ~/.config/openbox
echo "/home/pi/BeoSound5redux/setup/kiosk.sh" > ~/.config/openbox/autostart

echo "-------------------------------------------------------"
echo "Installation complete!"
echo "1. Run 'sudo raspi-config' and set to 'Console Autologin'."
echo "2. Add 'exec startx' to the end of your ~/.bashrc"
echo "3. Reboot to start the interface."
echo "-------------------------------------------------------"
