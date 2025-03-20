import socket

class tcp_util():
    """Utility class for tcp
    comunication management. """
    def __init__(self, ip, port):
        self.ip          = ip
        self.port        = port
        self.socket      = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)

        self.headerBytes = 8 

        self.connectSocket()
        pass

    def __del__ (self):
        """Desctuctor, closes socket"""
        try:
            self.closeSocket()
        except:
            pass

    def connectSocket(self):
        """Connects socket"""
        self.socket.connect((self.ip,self.port))
        pass

    def closeSocket(self):
        """Closes socket connection"""
        self.socket.close()
        pass

    def sendMessage(self,message):
        """Encodes message and sends it on socket"""
        encodedMessage = self.encodeMessage(message)
        self.socket.send(encodedMessage)
        pass

    def encodeMessage(self,message,pknumber=0):
        """Encodes message adding 4 bytes header"""
        messageLength = len(message) + self.headerBytes
        encodedMessage = (messageLength).to_bytes(4, byteorder='big') +  (pknumber).to_bytes(4, byteorder='big')  + message.encode('utf-8')
        print(encodedMessage)
        return encodedMessage


BUFFER_SIZE = 100000


from time import sleep
import paho.mqtt.client as paho
caencontroller="192.168.0.45"
controllerport=7000
broker="192.168.0.45"
brokerport=1883
psid="caen"
message="GetStatus,PowerSupplyId:%s"%psid
import json


def loop():
    """Send command on TCP socket
    """
    alarm=0
    while(True) :
      try:
        tcpClass = tcp_util(caencontroller,controllerport)
        tcpClass.sendMessage(message)
        data = b''
        while(True) :
            try:
                chunk = tcpClass.socket.recv(BUFFER_SIZE)[8:]
                if not chunk:
                    break
                data+=chunk
            except:
                break
        print(data[-10:])
        data=data.decode("utf-8")
        parsedData={}
        for token in data.split(',') :
            if token.startswith(psid):
                key,value=token.split(":")
                value=float(value)
                parsedData[key]=value
        #print(json.dumps(parsedData,indent=4),flush=True)
        mqttclient = paho.Client(paho.CallbackAPIVersion.VERSION1, "CAEN")
        mqttclient.connect(broker,brokerport)
        ret=mqttclient.publish("/caenstatus/full",json.dumps(parsedData))
        print("ok")
        sleep(1)
        if alarm > 5 :
           print("We are back" , alarm)
           mqttclient.publish("/alarm","CAEN is back (%s)"%alarm)
        alarm=0

      except Exception as e:
        print(e)
        alarm+=1
        if alarm % 60 == 6 :
          print("Sending alarm",alarm)
          mqttclient.publish("/alarm","Cannot receive or send data, CAEN is off or MQTT server down (%s)"%alarm)
        # retry first a few times
        if alarm > 3:
            print("Cannot receive or send data, CAEN is off or MQTT server down, sleeping 60 seconds",alarm,flush=True)
            sleep(60)
        else:
            sleep(1)
            print("Cannot receive or send data, CAEN is off or MQTT server down, retrying...",alarm,flush=True)

if __name__ == "__main__":
    print("caen-mqtt started",flush=True)
    loop()
