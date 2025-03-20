import json
import paho.mqtt.client as mqtt

broker = "192.168.0.45"
brokerport = 1883

client = mqtt.Client()
client.connect(broker, brokerport)

client.publish("/coldroom/cmd/set_light", json.dumps({"status": 1}))
