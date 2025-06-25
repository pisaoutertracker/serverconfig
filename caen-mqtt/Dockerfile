FROM python:3.10-alpine
RUN pip install paho-mqtt
RUN mkdir /scripts
WORKDIR /scripts
CMD ["python3","mqtt-caen.py"] 

#COPY mqtt-caen.py /scripts/mqtt-caen.py  
#CMD ["python3","/scripts/mqtt-caen.py"] 



#FROM library/almalinux
#RUN yum install -y vim wget git python3 epel-release
#RUN yum install -y python3-paho-mqtt
#RUN mkdir /scripts
#COPY mqtt-caen.py /scripts/mqtt-caen.py  
#CMD ["python3","/scripts/mqtt-caen.py"] 

