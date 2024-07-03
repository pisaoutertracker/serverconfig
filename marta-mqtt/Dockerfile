FROM python:3.11-alpine
RUN pip install paho-mqtt PyYaml transitions pymodbus==2.5.3
RUN mkdir /scripts
WORKDIR /scripts

CMD ["python3","marta.py","/marta_registers.yml"] 

