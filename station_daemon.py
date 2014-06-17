

#SEE https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/pyzmq/multisocket/tornadoeventloop.html
#for info on listeners

from config import *

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from rootio.extensions import db

import zmq
import json
import time
import sys
from multiprocessing import Process
import random
import redis

from zmq.eventloop import ioloop, zmqstream
ioloop.install()
MESSAGE_QUEUE_PORT_WEB = "5556"


# get access to telephony & web database
telephony_server = Flask("ResponseServer")
telephony_server.debug = True

from rootio.telephony.models import *
from rootio.radio.models import *

telephony_server.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
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
    def __init__(self, station_id):
        logger.info("Hello World")
        self.gateway = 'sofia/gateway/utl'
        self.caller_queue = []
        self.active_workers = []

        try:
            original = db.session.query(Station).filter(Station.id == station_id).one()
            print original
        except Exception, e:
            logger.error('Could not load one unique station', exc_info=True)
        #  copy database item to daemon item -- tried to automate this but couldn't make keys
        self.about = original.about
        self.name = original.name
        self.network_id = original.network_id
        self.cloud_phone_id = original.cloud_phone_id
        self.cloud_phone = original.cloud_phone
        self.frequency = original.frequency
        self.transmitter_phone_id = original.transmitter_phone_id
        self.transmitter_phone = original.transmitter_phone
        self.api_key = original.api_key
        self.location_id = original.location_id
        self.id = original.id
        self.owner_id = original.owner_id
        self.program = None
        self.outgoing_gateways = original.outgoing_gateways
        self.incoming_gateways = original.incoming_gateways

        try:
            self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        except Exception, e:
            logger.error('Could not open redis connection', exc_info=True)
        #   INITIATE OUTGOING NUMBERS HERE
        #   Hereafter, stations can do a r.rpoplpush('outgoing_unused','outgoing_busy') to get a number
        #   or a r.lrem('outgoing_busy', 0, somenumber) to return it -- SHOULD be atomic :(
        while self.r.rpop('outgoing_unused') != None:
            pass
        while self.r.rpop('outgoing_busy') != None:
            pass
        for i in range(OUTGOING_NUMBER_BOTTOM, OUTGOING_NUMBER_TOP+1):
            self.r.rpush('outgoing_unused', '0'+str(i))

        #   INITIATE IS_MASTER KEYS
        for k in self.r.keys('is_master_*'):
            self.r.set(k,'none')

        #  start listeners
        self.start_listeners()

########################################################################
#                   Listeners for messages on calls, sms, 
#                   program changes, and db updates
########################################################################

    # Listener function, running 
    def listener(self, channel, function):
        port = MESSAGE_QUEUE_PORT_WEB
        context = zmq.Context()
        socket_sub = context.socket(zmq.SUB)
        socket_sub.connect("tcp://localhost:%s" % port)
        socket_sub.setsockopt(zmq.SUBSCRIBE, str(channel))
        stream_sub = zmqstream.ZMQStream(socket_sub)
        stream_sub.on_recv(function)
        print "Connected to publisher with port %s" % port
        ioloop.IOLoop.instance().start()
        print "Worker has stopped processing messages."

    #https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/pyzmq/multisocket/tornadoeventloop.html
    def start_listeners(self):
        call_listener = Process(target=self.listener, args=(str('station.'+str(self.id)+'.call'), self.process_call))
        call_listener.start()
        self.active_workers.append(call_listener)

        sms_listener = Process(target=self.listener, args=(str('station.'+str(self.id)+'.sms'), self.process_sms))
        sms_listener.start()
        self.active_workers.append(sms_listener)

        program_listener = Process(target=self.listener, args=(str('station.'+str(self.id)+'.program'), self.process_program))
        program_listener.start()
        self.active_workers.append(program_listener)

        db_listener = Process(target=self.listener, args=(str('station.'+str(self.id)+'.db'), self.process_db))
        db_listener.start()
        self.active_workers.append(db_listener)

    #  respond to call-related messages
    def process_call(self, msg):
        logger.info("Processing call: {}".format(msg))

    #  respond to sms messages
    def process_sms(self, msg):
        logger.info("Processing sms: {}".format(msg))

    #  respond to program changes
    def process_program(self, msg):
        logger.info("Processing program: {}".format(msg))
        import news_report
        self.program = news_report.News(3, self)

    #  respond to db changes
    def process_db(self, msg):
        change_dict = json.loads(msg)
        logger.info("Processing db change: {}".format(change_dict))


# self test of message server to see if daemons are receiving
def test_receivers():
    port = MESSAGE_QUEUE_PORT_WEB
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)

    while True:
        message_topics = ['station.7.program', 'station.7.call','station.7.program', 'station.7.program','sms.station.6', 'call.station.6']
        topic = message_topics[random.randrange(0, len(message_topics))]
        dicked = {'this':'that',"if":'then', "1":1,"2":2}
        messagedata = json.dumps(dicked)
        print "%s %s" % (topic, messagedata)
        socket.send("%s %s" % (topic, messagedata))
        time.sleep(1)

#  Silly launch of fake daemons
#stations = db.session.query(Station).all()
#daemons = []
#for i in stations:
#    daemons.append(StationDaemon(i.id))
#test_receivers()

