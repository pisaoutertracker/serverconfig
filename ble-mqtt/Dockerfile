#FROM library/almalinux
#RUN yum install -y vim wget git python3 epel-release
#RUN yum install -y python3-paho-mqtt
#RUN yum groupinstall -y 'Development Tools'
#RUN yum install -y pip glib2-devel

#RUN mkdir /scripts
#COPY mqtt-caen.py /scripts/mqtt-caen.py  
#CMD ["python3","/scripts/mqtt-caen.py"] 


FROM python:3.7-alpine
RUN pip install paho-mqtt requests 
RUN apk add --update build-base glib-dev
RUN pip install switchbotmeter
RUN mkdir /scripts


COPY mqtt-ble.py /scripts/mqtt-ble.py  
CMD ["python3","/scripts/mqtt-ble.py"] 
#CMD ["sleep","3600"] 

