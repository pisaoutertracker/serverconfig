FROM library/almalinux
RUN yum install -y vim wget git python3 epel-release
RUN yum install -y python3-paho-mqtt
RUN mkdir /scripts
COPY mqtt-caen.py /scripts/mqtt-caen.py  
RUN python3 /scripts/mqtt-caen.py 
