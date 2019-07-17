#! /bin/sh

# Create a .desktop file in ~/.config/autostart
#
#[Desktop Entry]
#Name=IoTRefine
#GenericName=IoTRefine
#Comment=Refine for the smart home
#Exec=/path/to/this/script
#Terminal=false
#Type=Application
#X-GNOME-Autostart-enabled=true

echo Starting IoT-Refine, please be patient :D
sleep 30
chromium --start-fullscreen --app=http://localhost:4200 http://localhost:4200
