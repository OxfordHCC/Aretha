#! /bin/sh

# Add the followig to /etc/xdg/autostart/aretha.desktop
#
#[Desktop Entry]
#Name=IoTRefine
#Exec=/path/to/this/script
#Terminal=true
#Type=Application
#X-GNOME-Autostart-enabled=true

echo Starting IoT-Refine, please be patient :D
sleep 20
chromium --start-fullscreen --app=http://localhost:4200 http://localhost:4200
