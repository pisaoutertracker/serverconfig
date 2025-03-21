import os
import requests
import inspect
import time
import logging
import paho.mqtt.client as mqtt
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class ThermalStatus:
    """Class to get the status of the coldroom"""

    TOPIC_CMDS = "/coldroom/cmd/#"
    TOPIC_RESP = "/coldroom/alarm"
    TOPIC_ROOT = "/coldroom"
    TOPIC_ALARMS = "/alarm"

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
        # Start the session
        self.session = requests.Session()
        # Flag to check if the cookie session is active (default False)
        self.is_active = False

        # Command handlers
        self.command_handlers = {
            "set_temperature": self.set_temperature,
            "set_humidity": self.set_humidity,
            "control_light": self.control_light,
            "control_temperature": self.control_temperature,
            "control_humidity": self.control_humidity,
            "control_external_dry_air": self.control_external_dry_air,
            "run": self.run,
            "stop": self.stop,
        }

        # Interesting jsons
        self.selected_keys = [
            "light_door_status",
            "status",
            "dashboard",
            "manual/refresh",
        ]

    def parse(self, response):
        """Parse the response"""
        parsed_response = {}
        alarms = []
        for selected_key in self.selected_keys:
            if selected_key not in response:
                continue
            if selected_key == "light_door_status":
                # Check if this is the door open status
                parsed_response["CmdDoorUnlock_Reff"] = int(response[selected_key]["CmdDoorUnlock_Reff"])
            elif selected_key == "status":
                parsed_response["machine_time"] = response[selected_key]["machine_time"]
                parsed_response["light"] = int(response[selected_key]["light"])
                # Door status via alarm
                for alarm_dict in response[selected_key]["alarms"]:
                    if alarm_dict["name"] == "ALARM_06":
                        parsed_response["door_status"] = 1
                        break
                    else:
                        parsed_response["door_status"] = 0
                alarms = self.parse_alarms(response[selected_key]["alarms"])
            elif selected_key == "dashboard":
                parsed_response["running"] = response[selected_key]["running"]
                parsed_response["ch_temperature"] = {
                    "value": float(response[selected_key]["channels"]["Mis_CH0"]["VALUE"]),
                    "setpoint": float(response[selected_key]["channels"]["Mis_CH0"]["SETPOINT"]),
                    "status": int(response[selected_key]["channels"]["Mis_CH0"]["STATUS"]),
                }
                parsed_response["ch_humidity"] = {
                    "value": float(response[selected_key]["channels"]["Mis_CH1"]["VALUE"]),
                    "setpoint": float(response[selected_key]["channels"]["Mis_CH1"]["SETPOINT"]),
                    "status": int(response[selected_key]["channels"]["Mis_CH1"]["STATUS"]),
                }
            elif selected_key == "manual/refresh":
                parsed_response["dry_air_status"] = int(
                    (int(response[selected_key]["CONTACTS_D"]["DED"]) & (1 << 7)) != 0
                )

        return parsed_response, alarms

    def parse_alarms(self, alarms):
        """Parse the alarms"""
        parsed_alarms = []
        for alarm_dict in alarms:
            if alarm_dict["name"] == "ALARM_06":
                # Skip Door Open alarm
                continue
            timestamp = time.ctime(alarm_dict["timestamp"])
            eng_text = alarm_dict["text"]["English"]
            alarm_string = f"[MyKratos/Coldroom]({timestamp}) == {eng_text}"
            parsed_alarms.append(alarm_string)
        return parsed_alarms

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
        response = {}
        for json_name in self.selected_keys:
            url = f"{self.base_url}/spes.fcgi/{json_name}"
            try:
                raw_response = self.session.get(
                    url,
                    headers=self.headers,
                    verify=False,
                    cookies=self.session.cookies,
                )
                try:
                    response[json_name] = raw_response.json()
                except Exception as e:
                    logging.error(f"Error when decoding {json_name}: {e}")
            except Exception as e:
                logging.error(f"Error when getting {json_name}: {e}")
            time.sleep(1)
            logging.info(f"{json_name} retrieved")
        return response

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

        def on_connect(client, userdata, flags, rc):
            """On connect callback"""
            logging.info(f"Connected with result code {rc}")
            if rc == 0:
                logging.info("Connection successful")
                client.subscribe(self.TOPIC_CMDS)
            else:
                logging.error(f"Connection failed with result code {rc}")

        def on_disconnect(client, userdata, rc):
            """On disconnect callback"""
            if rc != 0:
                logging.error(f"Unexpected disconnection: {rc}")
            else:
                logging.info("Disconnected")

        def on_message(client, userdata, message):
            """On message callback"""
            try:
                command = message.topic.split("/")[-1]
                function = self.command_handlers[command]
                function_args = inspect.getfullargspec(function).args
                if "value" in function_args:
                    value = message.payload.decode()
                    function(float(value))
                else:
                    function()
            except Exception as e:
                logging.error(f"Error: {e}")
                # self.publish_response(client, command, {"status": "error", "message": str(e)})

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "COLDROOM")
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        client.connect(broker, brokerport)
        return client

    def publish_response(self, client, command, response):
        """Publish the response to the mqtt broker"""
        topic = f"{self.TOPIC_RESP}/{command}"
        client.publish(topic, json.dumps(response))

    def control_light(self, value):
        """Set the light of the coldroom"""
        url = f"{self.base_url}/spes.fcgi/setvars?v289={value}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Light set to {value}")
        return response

    def set_temperature(self, value):
        """Set the temperature of the coldroom"""
        url = f"{self.base_url}/spes.fcgi/setvars?v380={value}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Temperature set to {value} C")
        return response

    def set_humidity(self, value):
        """Set the humidity of the coldroom"""
        url = f"{self.base_url}/spes.fcgi/setvars?v382={value}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Humidity set to {value} %")
        return response

    def control_temperature(self, value):
        """Control the temperature of the coldroom"""
        url = f"{self.base_url}/spes.fcgi/setvars?v365={value}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Temperature control set to {value}")
        return response

    def control_humidity(self, value):
        url = f"{self.base_url}/spes.fcgi/setvars?v366={value}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Humidity control set to {value}")
        return response

    def control_external_dry_air(self, value):
        url = f"{self.base_url}/spes.fcgi/setvars?v363={value}"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"External dry air control set to {value}")
        return response

    def run(self):
        url = f"{self.base_url}/spes.fcgi/chamber/run"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Chamber run")
        return response

    def stop(self):
        url = f"{self.base_url}/spes.fcgi/chamber/stop"
        response = self.session.get(url, headers=self.headers, verify=False, cookies=self.session.cookies)
        logging.info(f"Chamber stop")
        return response

    def loop(self, client):
        """Run the loop"""
        client.loop_start()
        self.login_session()
        last_published_alarms = {}
        while True:
            active = self.check_status()
            if active:
                response = self.get_status()
                parsed_response, current_alarms = self.parse(response)
                client.publish(f"{self.TOPIC_ROOT}/state", json.dumps(parsed_response))
                if current_alarms:
                    current_alarms_id = []
                    current_time = time.time()
                    for alarm in current_alarms:
                        alarm_id = alarm.split("==")[-1].strip()
                        current_alarms_id.append(alarm_id)
                        if alarm_id not in last_published_alarms:
                            last_published_alarms[alarm_id] = current_time
                            client.publish(self.TOPIC_ALARMS, alarm)
                        else:
                            last_time = last_published_alarms[alarm_id]
                            if current_time - last_time > 3600:
                                last_published_alarms[alarm_id] = current_time
                                client.publish(self.TOPIC_ALARMS, alarm)
                    for existing_id in last_published_alarms:
                        if existing_id not in current_alarms_id:
                            del last_published_alarms[existing_id]
                time.sleep(1)
            else:
                self.authenticate()


broker = "192.168.0.45"
brokerport = 1883

if __name__ == "__main__":

    coldroom = ThermalStatus()
    client = coldroom.connect_mqtt(broker, brokerport)
    coldroom.loop(client)
