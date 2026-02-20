#!/bin/bash

# Disable screen blanking
xset s off
xset s noblank
xset -dpms

# Hide the mouse cursor
unclutter -idle 0.1 -root &

# Launch Chromium in Kiosk mode
# --no-first-run and --no-default-browser-check avoid popups
# --incognito ensures a clean state
chromium-browser 
  --noerrdialogs 
  --disable-infobars 
  --kiosk 
  --no-first-run 
  --no-default-browser-check 
  --incognito 
  http://localhost:4200
