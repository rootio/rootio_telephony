#!/bin/bash
screen -S redis_server -dm sudo /usr/local/Cellar/redis/2.8.13/bin/redis-server /usr/local/etc/redis.conf
echo "launched redis... sleeping for a second..."
sleep 1
screen -S freeswitch -dm /usr/local/freeswitch/freeswitch
echo "launched freeswitch"

cd /usr/local/plivo
screen -S plivo-rest -dm /usr/local/plivo/bin/plivo-rest
screen -S plivo-outbound -dm /usr/local/plivo/bin/plivo-outbound
screen -S plivo-cache -dm /usr/local/plivo/bin/plivo-cache
echo "launced three plivo processes -- rest, outbout, cache"

cd /Users/csik/Documents/code/rootio/rootio_web/scheduler
source vnv/bin/activate
screen -S forwarder.py -dm /Users/csik/Documents/code/rootio/rootio_web/vnv/bin/python forwarder_device.py
echo "Launched forwarder.py"

screen -S run.py -dm /Users/csik/Documents/code/rootio/rootio_web/vnv/bin/python run.py
echo "Launched run.py"

cd /Users/csik/Documents/code/rootio/rootio_telephony
source vnv/bin/activate
screen -S telephony_server.py -dm  /Users/csik/Documents/code/rootio/rootio_telephony/vnv/bin/python telephony_server.py
echo "launched telephony server"

screen -S launch_stations.py -dm /Users/csik/Documents/code/rootio/rootio_telephony/vnv/bin/python launch_stations.py
echo "launched stations"

set -x #echo on
screen -ls

