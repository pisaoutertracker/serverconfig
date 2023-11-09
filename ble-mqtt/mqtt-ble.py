import time
import json
import paho.mqtt.client as paho
from switchbotmeter import DevScanner

broker = "192.168.0.45"
brokerport = 1883


def ble_status():
    json_status = {}
    try:
        for current_devices in DevScanner():
            for device in current_devices:
                if device.temp:
                    print(json_status)
                    mqqttclient = paho.Client("BLE")
                    mqqttclient.connect(broker, brokerport)
                    ret = mqqttclient.publish(
                        f"/ble/{device.device.addr}", json.dumps(json_status)
                    )
                    print(ret)
    except:
        print("Error in loop", flush=True)
        time.sleep(60)


if __name__ == "__main__":
    ble_status = ble_status()
