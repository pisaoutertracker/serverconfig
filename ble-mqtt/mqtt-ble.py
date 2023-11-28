import logging
import yaml
import json
import paho.mqtt.client as paho
from switchbotmeter import DevScanner


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

with open("ble_names.yaml", "r") as f:
    names = yaml.safe_load(f)

broker = "192.168.0.45"
brokerport = 1883

goodkeys = ["temp", "humidity"]


def ble_status():
    for current_devices in DevScanner():
        for device in current_devices:
            if device.temp:
                device_name = names[device.device.addr]
                mqqttclient = paho.Client("BLE")
                mqqttclient.connect(broker, brokerport)
                msg = json.dumps(
                    dict(filter(lambda x: x[0] in goodkeys, device.data.items()))
                )
                ret = mqqttclient.publish(f"/ble/{device.device.addr}", msg)
                logging.info(f"{device_name} ({device.device.addr}) {msg}")


if __name__ == "__main__":
    ble_status = ble_status()
