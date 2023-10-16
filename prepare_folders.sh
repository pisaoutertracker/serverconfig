#!/bin/bash
. pisaoutertracker.env
mkdir -p ${DATA_PREFIX}/testnode
mkdir -p ${DATA_PREFIX}/mosquitto/log
mkdir -p ${DATA_PREFIX}/mosquitto/data/
mkdir -p ${DATA_PREFIX}/influxdb/influxdb-data
mkdir -p ${DATA_PREFIX}/grafana/grafana-data

chmod 777 ${DATA_PREFIX}/testnode
chmod 777 ${DATA_PREFIX}/mosquitto/log
chmod 777 ${DATA_PREFIX}/mosquitto/data/
chmod 777 ${DATA_PREFIX}/influxdb/influxdb-data
chmod 777 ${DATA_PREFIX}/grafana/grafana-data

