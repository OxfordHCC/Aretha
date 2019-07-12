#! /bin/sh

nmcli r wifi off #turn wifi off
sleep 1
nmcli r wifi on #turn wifi on
sleep 1
nmcli d wifi hotspot ifname wlp1s0 ssid "IoT Refine" password "wheresmydata" #start hotspot on built-in wifi card
sleep 1
