#! /bin/sh

nmcli r wifi off #turn wifi off
sleep 1
nmcli r wifi on #turn wifi on
sleep 1
nmcli d wifi hotspot ifname wlp58s0 ssid iotrefine password password123 #start hotspot on built-in wifi card
sleep 1
