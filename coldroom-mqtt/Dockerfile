FROM python:3.10-alpine
RUN pip install paho-mqtt requests
RUN mkdir /scripts
#COPY mqtt-coldroom.py /scripts/mqtt-coldroom.py  
WORKDIR /scripts
CMD ["python3","/scripts/mqtt-coldroom.py"] 
