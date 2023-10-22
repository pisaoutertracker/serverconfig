#!/bin/bash
. pisaoutertracker.env
mkdir -p ${DATA_PREFIX}/testnode
mkdir -p ${DATA_PREFIX}/mosquitto/log
mkdir -p ${DATA_PREFIX}/mosquitto/data/
mkdir -p ${DATA_PREFIX}/influxdb/influxdb-data
mkdir -p ${DATA_PREFIX}/grafana/grafana-data
mkdir -p ${DATA_PREFIX}/MongoDB/data

chown dockeruser.dockeruser -R ${DATA_PREFIX}

