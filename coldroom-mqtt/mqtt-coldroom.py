import os
import requests
import time
import logging
import paho.mqtt.client as paho
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class ThermalStatus:
    """Class to get the status of the coldroom"""

    TOPIC_CMDS = "/coldroom/cmd"
    TOPIC_RESP = "/coldroom/alarm"
    TOPIC_ROOT = "/coldroom"

    def __init__(self):
        # Base url of the coldroom webserver
        self.base_url_1 = "http://192.168.0.254"  # cabled
        self.base_url_2 = "http://11.0.0.1"  # wifi
        # Headers for the requests
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        # Dict of the jsons to get
        # TODO: parse or filter the jsons to get only the interesting data
        # NOTE: string are not sent to the mqtt broker
        self.json_interesting_dict = {
            "light_door_status": [],
            "status": [],
            "dashboard": [],
            "refresh": [],
        }
        # Start the session
        self.session = requests.Session()
        # Flag to check if the cookie session is active (default False)
        self.is_active = False

        # Command handlers
        self.command_handlers = {
            "set_temperature": self.set_temperature,
            "set_humidity": self.set_humidity,
            "set_light": self.set_light,
        }

    def login_session(self):
        """Login to the session"""
        login_url = "{base_url}/httpd_auth.fcgi/accounts/login/"
        try:
            login_response = self.session.get(
                login_url.format(base_url=self.base_url_1), headers=self.headers, verify=False
            )
            self.base_url = self.base_url_1
        except requests.exceptions.ConnectionError:
            login_response = self.session.get(
                login_url.format(base_url=self.base_url_2), headers=self.headers, verify=False
            )
            self.base_url = self.base_url_2
        logging.info("Session started")

        return login_response

    def authenticate(self):
        """Authenticate to the session"""
        auth_url = f"{self.base_url}/httpd_auth.fcgi/accounts/authenticate/"
        # Login data
        login_data = {
            "username": os.environ.get("COLDROOM_USERNAME"),
            "password": os.environ.get("COLDROOM_PASSWORD"),
        }
        if not login_data["username"] or not login_data["password"]:
            logging.error("Username or password not set")
            raise ValueError

        auth_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRFToken": self.session.cookies["csrftoken"],
            "Referer": f"{self.base_url}/main.html",
            "Origin": self.base_url,
        }
        self.session.headers.update(auth_headers)

        auth_response = self.session.post(auth_url, json=login_data, verify=False, cookies=self.session.cookies)
        try:
            self.session.cookies["sessionid"]
        except KeyError:
            logging.error("Authentication failed")
            raise

        logging.info("Authenticated")

        return auth_response

    def get_status(self):
        """Get the status of the coldroom"""
        status_response_list = []
        for json_name in self.json_interesting_dict.keys():
            url = f"{self.base_url}/spes.fcgi/{json_name}"
            status_response = self.session.get(
                url,
                headers=self.headers,
                verify=False,
                cookies=self.session.cookies,
            )
            time.sleep(1)
            status_response_list.append(status_response.json())
            logging.info(f"{json_name} retrieved")
        return status_response_list

    def check_status(self):
        """Check if the session is active"""
        for cookie in self.session.cookies:
            if cookie.name == "sessionid":
                expiration_time = cookie.expires
                if time.time() > expiration_time:
                    logging.info("Session expired")
                    self.is_active = False
                else:
                    if not self.is_active:
                        self.is_active = True
                        logging.info(f"Session active: expires {time.ctime(expiration_time)}")
        return self.is_active

    def connect_mqtt(self, broker, brokerport):
        """Connect to the mqtt broker"""
        mqttclient = paho.Client(paho.CallbackAPIVersion.VERSION1, "COLDROOM")
        mqttclient.connect(broker, brokerport)
        return mqttclient

    def on_connect(self, client, userdata, flags, rc):
        """On connect callback"""
        logging.info(f"Connected with result code {rc}")
        if rc == 0:
            logging.info("Connection successful")
            client.subscribe(self.TOPIC_CMDS)
            # client.publish(f"/coldroom/status")
        else:
            logging.error(f"Connection failed with result code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """On disconnect callback"""
        if rc != 0:
            logging.error(f"Unexpected disconnection: {rc}")
        else:
            logging.info("Disconnected")

    def on_message(self, client, userdata, message):
        """On message callback"""
        try:
            command = message.topic.split("/")[-1]
            payload = json.loads(message.payload)
            self.command_handlers[command](payload)
        except Exception as e:
            logging.error(f"Error: {e}")
            self.publish_response(client, command, {"status": "error", "message": str(e)})

    def publish_response(self, client, command, response):
        """Publish the response to the mqtt broker"""
        topic = f"{self.TOPIC_RESP}/{command}"
        client.publish(topic, json.dumps(response))

    def set_light(self, payload):
        """Set the light of the coldroom"""
        # Example of url http://localhost:1080/spes.fcgi/setvars?v289=1
        url = f"{self.base_url}/spes.fcgi/setvars?v289={payload['status']}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Light set to {payload['status']}")
        return response

    def set_temperature(self, payload):
        url = f"{self.base_url}/spes.fcgi/setvars?v380={payload['value']}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Temperature set to {payload['value']}")
        return response

    def set_humidity(self, payload):
        url = f"{self.base_url}/spes.fcgi/setvars?v382={payload['value']}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Humidity set to {payload['value']}")
        return response

    def loop(self, client):
        """Run the loop"""
        self.login_session()
        while True:
            active = self.check_status()
            if active:
                status_list = self.get_status()
                for status, publish_topic in zip(status_list, list(self.json_interesting_dict.keys())):
                    ret = client.publish(f"/coldroom/{publish_topic}", json.dumps(status))
                time.sleep(1)
            else:
                self.authenticate()


broker = "192.168.0.45"
brokerport = 1883

if __name__ == "__main__":

    coldroom = ThermalStatus()
    client = coldroom.connect_mqtt(broker, brokerport)
    coldroom.loop(client)
