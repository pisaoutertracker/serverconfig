#FROM library/almalinux
#RUN yum install -y vim wget git python3 epel-release
#RUN yum install -y python3-paho-mqtt
#RUN yum groupinstall -y 'Development Tools'
#RUN yum install -y pip glib2-devel

#RUN mkdir /scripts
#COPY mqtt-caen.py /scripts/mqtt-caen.py  
#CMD ["python3","/scripts/mqtt-caen.py"] 


FROM python:3.11-alpine
RUN pip install paho-mqtt requests 
RUN apk add --update build-base glib-dev
RUN pip install switchbotmeter
RUN pip install PyYAML
RUN mkdir /scripts
WORKDIR /scripts

CMD ["python3","mqtt-ble.py"] 
#CMD ["sleep","3600"] 

