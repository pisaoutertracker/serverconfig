import time
import json
import paho.mqtt.client as paho
from switchbotmeter import DevScanner

broker = "192.168.0.45"
brokerport = 1883

goodkeys=["temp","humidity"]
def ble_status():
#    try:
        for current_devices in DevScanner():
            for device in current_devices:
                if device.temp:
                    mqqttclient = paho.Client("BLE")
                    mqqttclient.connect(broker, brokerport)
                    ret = mqqttclient.publish(
                        f"/ble/{device.device.addr}", json.dumps(dict(filter(lambda x: x[0] in goodkeys, device.data.items())))
                    )
                    print(ret)
#    except:
#        print("Error in loop", flush=True)
#        time.sleep(60)


if __name__ == "__main__":
    ble_status = ble_status()
