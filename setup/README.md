# BeoSound 5 Redux - Raspberry Pi Setup

This folder contains the necessary scripts and configuration files to turn your Raspberry Pi 5 into a dedicated BeoSound 5 controller.

## Deployment Steps

1.  **Clone the Repository:**
    Clone this project to `/home/pi/BeoSound5redux` on your Pi.

2.  **Run the Installer:**
    ```bash
    cd /home/pi/BeoSound5redux/setup
    chmod +x install.sh
    ./install.sh
    ```
    This script will:
    - Install Chromium, Xorg, Openbox, and other UI tools.
    - Set up the Python virtual environment and install backend dependencies.
    - Build the Angular production bundle.
    - Install and enable the `beosound-backend` and `beosound-frontend` systemd services.

3.  **Configure Auto-Login:**
    - Run `sudo raspi-config`.
    - Go to **System Options** > **Boot / Auto Login**.
    - Select **Console Autologin**.

4.  **Enable Kiosk on Boot:**
    Add the following line to the very end of your `/home/pi/.bashrc` file:
    ```bash
    [[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && exec startx -- -nocursor
    ```

5.  **Reboot:**
    ```bash
    sudo reboot
    ```

## Maintenance

- **Restart Backend:** `sudo systemctl restart beosound-backend`
- **Restart Frontend:** `sudo systemctl restart beosound-frontend`
- **View Logs:** `journalctl -u beosound-backend -f`
