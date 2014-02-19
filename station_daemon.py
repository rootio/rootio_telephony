

#SEE https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/pyzmq/multisocket/tornadoeventloop.html
#for info on listeners

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from rootio.extensions import db

import zmq
import time
import sys
from multiprocessing import Process
import random

from zmq.eventloop import ioloop, zmqstream
ioloop.install()

# get access to telephony & web database
telephony_server = Flask("ResponseServer")
telephony_server.debug = True

from rootio.telephony.models import *
from rootio.radio.models import *

telephony_server.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:NLPog1986@localhost'
db = SQLAlchemy(telephony_server)

# logging
import logging

try:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # create a file handler
    handler = logging.FileHandler('logs/telephony.log', mode='a')
    handler.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(ch)
except Exception, e:
    logger.error('Failed to open logger', exc_info=True)


#for realz, create daemon class
class StationDaemon(Station):
    def __init__(self, id):
        logger.info("Hello World")
        self.gateway = 'sofia/gateway/utl'
        self.caller_queue = []
        self.active_workers = []

        try:
            original = db.session.query(Station).filter(Station.id == id).one()
            print original
        except Exception, e:
            logger.error('Could not load one unique station', exc_info=True)
            print 'Could not load one unique station'
        #  copy database item to daemon item -- tried to automate this but couldn't make keys
        self.about = original.about
        self.name = original.name
        self.network_id = original.network_id
        self.cloud_phone_id = original.cloud_phone_id
        self.frequency = original.frequency
        self.transmitter_phone_id = original.transmitter_phone_id
        self.api_key = original.api_key
        self.location_id = original.location_id
        self.id = original.id
        self.owner_id = original.owner_id

        #  start listeners
        self.start_listeners()

    #  start listeners - so far just a test section
    def start_listeners(self):
        sms_listener = Process(target=self.listener, args=(str('sms.station.'+str(self.id)), self.process_message))
        sms_listener.start()
        self.active_workers.append(sms_listener)
        call_listener = Process(target=self.listener, args=(str('call.station.'+str(self.id)), self.process_message))
        call_listener.start()
        self.active_workers.append(call_listener)

    #  generic process, replace with sms, call, load program, etc.
    def process_message(self, msg):
        print "Processing ... %s" % msg
        #m = msg[0].split(' ',1)[1]
        #print pickle.loads(m)

    def listener(self, channel, function):
        port = "5557"
        context = zmq.Context()
        socket_sub = context.socket(zmq.SUB)
        socket_sub.connect("tcp://localhost:%s" % port)
        socket_sub.setsockopt(zmq.SUBSCRIBE, str(channel))
        stream_sub = zmqstream.ZMQStream(socket_sub)
        stream_sub.on_recv(function)
        print "Connected to publisher with port %s" % port
        ioloop.IOLoop.instance().start()
        print "Worker has stopped processing messages."

#    def load_program():
#
#    def load_episode():
#
#    def queue_episode():
#
#    def cleanup():

# testing message server to see if daemons are receiving
def test_receivers():
    port = "5557"
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)

    while True:
        message_topics = ['sms.station.7', 'call.station.7','sms.station.5', 'call.station.5','sms.station.6', 'call.station.6']
        topic = message_topics[random.randrange(0, len(message_topics))]
        messagedata = random.randrange(1, 215) - 80
        print "%s %s" % (topic, str(messagedata))
        socket.send("%s %s" % (topic, messagedata))
        time.sleep(1)

# Silly launch of fake daemons
stations = db.session.query(Station).all()
daemons = []
for i in stations:
    daemons.append(StationDaemon(i.id))
test_receivers()

