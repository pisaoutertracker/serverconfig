import logging
import yaml
import json
import paho.mqtt.client as paho
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

def ble_status():
    """Scan for BLE devices and publish their data to MQTT"""
    for current_devices in DevScanner():
        for device in current_devices:
            # Check if the device is ours 
            if device.temp and device.model == "T" and device.mode == "00":
                # Check if we know the device name
                if device.device.addr in names:
                    device_name = names[device.device.addr]
                else:
                    logging.error(f"Unknown device: {device.device.addr}")
                    logging.error(f"{device.data}")
                    raise KeyError
                # Publish the data to MQTT
                mqqttclient = paho.Client("BLE")
                mqqttclient.connect(broker, brokerport)
                # Only publish the keys we want
                msg = json.dumps(
                    dict(filter(lambda x: x[0] in goodkeys, device.data.items()))
                )
                ret = mqqttclient.publish(f"/ble/{device.device.addr}", msg)
                logging.info(f"{device_name} ({device.device.addr}) {msg}")


if __name__ == "__main__":
    ble_status = ble_status()
