import os
import requests
import time


class thermal_status:
    """Class to get the status of the thermal chamber"""

    def __init__(self):
        self.base_url = "http://11.0.0.1"
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.json_interesting_dict = {
            "light_door_status": [],
            "status": [],
            "dashboard": [],
        }

        self.session = requests.Session()
        self.is_active = False

    def login_session(self):
        print("Logging in...")
        login_url = f"{self.base_url}/httpd_auth.fcgi/accounts/login/"
        try:
            login_response = self.session.get(
                login_url, headers=self.headers, verify=False
            )
            print("Login successful with status code", login_response.status_code)
            return login_response
        except:
            print("Login failed")

    def authenticate(self):
        print("Authenticating...")
        auth_url = f"{self.base_url}/httpd_auth.fcgi/accounts/authenticate/"
        try:
            login_data = {
                "username": os.environ.get("THERMAL_USERNAME"),
                "password": os.environ.get("THERMAL_PASSWORD"),
            }
        except:
            print("Credentials not found")

        try:
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
            if auth_response.status_code == 200:
                self.is_active = True
                print(
                    "Authentication successful with status code",
                    auth_response.status_code,
                )
            return auth_response
        except:
            print("Authentication failed")

    def get_status(self):
        print("Getting status...")
        status_response_list = []
        try:
            for json_name in self.json_interesting_dict.keys():
                url = f"{self.base_url}/spes.fcgi/{json_name}"
                status_response = self.session.get(
                    url,
                    headers=self.headers,
                    verify=False,
                    cookies=self.session.cookies,
                )
                # print(status_response.json())
                time.sleep(1)
                status_response_list.append(status_response.json())
            print("Status retrieved")
            return status_response_list
        except:
            print("Error in getting status")

    def check_status(self):
        try:
            for cookie in self.session.cookies:
                if cookie.name == "sessionid":
                    expiration_time = cookie.expires
                    # expiration_time = time.time() - 5  # 5s test
                    if time.time() > expiration_time:
                        self.is_active = False
                    else:
                        self.is_active = True
            return self.is_active
        except:
            print("Error in checking status")


import paho.mqtt.client as paho
import json

broker = "192.168.0.45"
brokerport = 1883
publish_topic_list = ["lightdoor", "status", "dashboard"]


def loop():
    print("Loop started...", flush=True)
    therm = thermal_status()
    therm.login_session()
    while True:
        try:
            active = therm.check_status()
            if active:
                status_list = therm.get_status()
                for status, publish_topic in zip(status_list, publish_topic_list):
                    print(json.dumps(status, indent=4), flush=True)
                    mqttclient = paho.Client("COLDROOM")
                    mqttclient.connect(broker, brokerport)
                    ret = mqttclient.publish(
                        f"/coldroom/{publish_topic}", json.dumps(status)
                    )  # signle json dump?
                    print(ret)
                time.sleep(10)
            else:
                therm.authenticate()
                time.sleep(5)

        except:
            print("Error in loop", flush=True)
            time.sleep(60)


if __name__ == "__main__":
    loop()
