#!/bin/sh

while /bin/true; do 

  while  ping -c 1 192.168.0.102 ; do
    echo "CAEN is reachable, starting server"
    power_supply/bin/PowerSupplyController -c  /config.xml
    sleep 5
  done

echo "CAEN cannot be reached, trying again in 60 seconds"
sleep 60

done
