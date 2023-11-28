FROM python:3.7-alpine
RUN pip install paho-mqtt requests
RUN mkdir /scripts
COPY mqtt-coldroom.py /scripts/mqtt-coldroom.py  
CMD ["python3","/scripts/mqtt-coldroom.py"] 

