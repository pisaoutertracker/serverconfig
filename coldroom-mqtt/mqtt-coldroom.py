import os
import requests
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class ThermalStatus:
    """Class to get the status of the coldroom"""

    def __init__(self):
        # Base url of the coldroom webserver
        self.base_url = "http://11.0.0.1"
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
        }
        # Start the session
        self.session = requests.Session()
        # Flag to check if the cookie session is active (default False)
        self.is_active = False

    def login_session(self):
        """Login to the session"""
        login_url = f"{self.base_url}/httpd_auth.fcgi/accounts/login/"
        login_response = self.session.get(login_url, headers=self.headers, verify=False)
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

        auth_response = self.session.post(
            auth_url, json=login_data, verify=False, cookies=self.session.cookies
        )
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


import paho.mqtt.client as paho
import json

broker = "192.168.0.45"
brokerport = 1883
publish_topic_list = ["lightdoor", "status", "dashboard"]


def loop():
    """Daemon"""
    # Start the session
    therm = ThermalStatus()
    therm.login_session()
    while True:
        active = therm.check_status()
        if active:
            status_list = therm.get_status()
            for status, publish_topic in zip(status_list, publish_topic_list):
                mqttclient = paho.Client("COLDROOM")
                mqttclient.connect(broker, brokerport)
                ret = mqttclient.publish(
                    f"/coldroom/{publish_topic}", json.dumps(status)
                )
            time.sleep(1)
        else:
            therm.authenticate()

if __name__ == "__main__":
    loop()
