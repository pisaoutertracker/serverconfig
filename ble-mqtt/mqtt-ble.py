import logging
import yaml
import json
import paho.mqtt.client as paho
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes 
import binascii,struct

from switchbotmeter import DevScanner


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load the names of the devices from a yaml file
with open("ble_names.yaml", "r") as f:
    names = yaml.safe_load(f)
# MQTT
broker = "192.168.0.45"
brokerport = 1883
# Only publish these keys
goodkeys = ["temp", "humidity"]

publish_properties = Properties(PacketTypes.PUBLISH)
publish_properties.MessageExpiryInterval = 60

def ble_status():
    """Scan for BLE devices and publish their data to MQTT"""
    for current_devices in DevScanner():
        for device in current_devices:
            # Check if the device is ours
            msg=""
            if device.temp and device.model == "T" and device.mode == "00":
                # Check if we know the device name
                if device.device.addr in names:
                    device_name = names[device.device.addr]
                else:
                    logging.error(f"Unknown device: {device.device.addr}")
                    logging.error(f"{device.data}")
                    raise KeyError
                # Publish the data to MQTT
                msg = json.dumps(
                    dict(filter(lambda x: x[0] in goodkeys, device.data.items()))
                )
            else:
              if device is not None:
                  for _, key, value in device.device.getScanData():
                      if key=="Manufacturer" :
                          hexv = binascii.unhexlify(value)
                          raw=bytearray(hexv)
                          if value[:4]=="d506": #Sensiron CO2 sensor
                                if device.device.addr in names:
                                     device_name = names[device.device.addr]
                                else :
                                    device_name= "Sensiron CO2 ble:"+device.device.addr

                                temp_ticks, humidity_ticks, co2 = struct.unpack("<HHH", raw[6:12])
                                if  temp_ticks !=0 and co2!= 0:
                                   temp = -45 + ((175.0 * temp_ticks) / (2**16 - 1))
                                   humidity = (100.0 * humidity_ticks) / (2**16 - 1)
                                msg="{"+f'"CO2":{co2},"temp":{temp},"humidity":{humidity}'+"}"
                                print(msg)

            if msg != "":    
                mqqttclient = paho.Client(paho.CallbackAPIVersion.VERSION1, "BLE")
                mqqttclient.connect(broker, brokerport)
                # Only publish the keys we want
                ret = mqqttclient.publish(f"/ble/{device_name}", msg,retain=True,  properties=publish_properties)
                logging.info(f"{device_name} ({device.device.addr}) {msg}")


if __name__ == "__main__":
    ble_status = ble_status()
