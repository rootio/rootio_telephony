

# SEE https://learning-0mq-with-pyzmq.readthedocs.org/en/
#            latest/pyzmq/multisocket/tornadoeventloop.html
# for info on listeners

from config import *

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from rootio.extensions import db

import zmq
from utils import ZMQ, init_logging
import json
import time
import sys
from multiprocessing import Process
import random
import redis
import isodate
from datetime import datetime

from zmq.eventloop import ioloop, zmqstream
ioloop.install()
MESSAGE_QUEUE_PORT_WEB = ZMQ_FORWARDER_SPITS_OUT

# get access to telephony & web database
telephony_server = Flask("ResponseServer")
telephony_server.debug = True

from rootio.telephony.models import *
from rootio.radio.models import *

telephony_server.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(telephony_server)

logger = init_logging('station_daemon')


# Daemon class
class StationDaemon(Station):

    """Docstring test."""

    def __init__(self, station_id):
        logger.info("Hello World")
        self.gateway = 'sofia/gateway/utl'
        self.caller_queue = []
        self.active_workers = []
        self.listener_reponses = {
            "call":               self.process_call,
            "sms":                self.process_sms,
            "program":            self.process_program,
            "db":                 self.process_db,
            "telephony_callback": self.process_telephony_callback,
            "digits":             self.process_digits,
            }


        try:
            self.station = db.session.query(Station).filter(
                Station.id == station_id).one()
        except Exception as e:
            logger.error('Could not load one unique station', exc_info=True)
        logger.info("Initializing station: {}".format(self.station.name))
        # This is for UTL outgoing ONLY.  Should be moved to a utility just for
        # the gateway, or such.
        try:
            self.r = redis.StrictRedis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=OUTGOING_NUMBERS_REDIS_DB)
        except Exception as e:
            logger.error('Could not open redis connection', exc_info=True)
        #   INITIATE OUTGOING NUMBERS HERE
        #   Hereafter, stations can do a r.rpoplpush('outgoing_unused','outgoing_busy') to get a number
        # or a r.lrem('outgoing_busy', 0, somenumber) to return it -- SHOULD be
        # atomic :(
        while self.r.rpop('outgoing_unused') is not None:
            pass
        while self.r.rpop('outgoing_busy') is not None:
            pass
        for i in range(OUTGOING_NUMBER_BOTTOM, OUTGOING_NUMBER_TOP+1):
            self.r.rpush('outgoing_unused', '0'+str(i))

        #   INITIATE IS_MASTER KEYS
        for k in self.r.keys('is_master_*'):
            self.r.set(k, 'none')

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
        socket_sub.connect(ZMQ_FORWARDER_SPITS_OUT)
        socket_sub.setsockopt(zmq.SUBSCRIBE, str(channel))
        stream_sub = zmqstream.ZMQStream(socket_sub)
        stream_sub.on_recv(function)
        logger.info("Station daemon listener connected to publisher with port {}".format(port))
        ioloop.IOLoop.instance().start()
        logger.info("Station daemon listener has stopped processing messages.")

    # https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/pyzmq/multisocket/tornadoeventloop.html
    def start_listeners(self):
        generic_listener = Process(
            target=self.listener,
            args=(
                str('station.' + str(self.station.id) + '.'),
                self.process_generic
                )
            )
        generic_listener.start()
        self.active_workers.append(generic_listener)

    def process_generic(self, msg):
        logger.info("Processing message to station: {}".format(msg))
        message_body = json.loads(msg[1])
        logger.info("Message body: {}".format(message_body))
        message_topic = msg[0]
        logger.info("Message topic: {}".format(message_topic))

        try:
            # message_specific is everything after station.number, as a list
            message_specific = message_topic.split('.')[2:]
            logger.info("Message specific: {}".format(message_specific))
            self.listener_reponses[
                message_specific[0]](
                message_specific,
                message_body)
        except Exception as e:
            logger.error(
                'Could not jump to listener_response in station_daemon.process_generic',
                exc_info=True)

    #  respond to call-related messages
    def process_call(self, topic, body):
        logger.info("Processing call: {}".format(body))

    #  respond to sms messages
    def process_sms(self, topic, body):
        logger.info("Processing sms: {}".format(body))

    #  respond to program changes
    def process_program(self, topic, body):
        logger.info("Processing program: {}".format(body))
        import news_report
        logger.info("for station {}".format(self.station.name))
        self.program = news_report.News(3, self)

    #  respond to db changes
    def process_db(self, topic, body):
        change_dict = body
        logger.info("Processing db change: {}".format(change_dict))
        logger.info("about to test if conditions right to launch a program")
        if (change_dict['operation'] == 'insert' or change_dict['operation'] == 'update') and isodate.parse_datetime(change_dict['start_time']) <= datetime.now():
            logger.info("We have successful conditions to launch a program!")
            import news_report
            self.program = news_report.News(3, self)
            # this should really be a callback! see below for
            # process_connected_transmitter()
            time.sleep(13)
            #  This used to call the difference sections of the news report
            #  but now they are daisy-chaining to each other
            self.program.go_intro()

    #  respond to successful connect to transmitter phone
    def process_telephony_callback(self, topic, body):
        pass

    #  respond to interactive digits (probably from program host)
    def process_digits(self, topic, body):
        pass

# self test of message server to see if daemons are receiving


def test_receivers():
    port = MESSAGE_QUEUE_PORT_WEB
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)

    while True:
        message_topics = [
            'station.7.program',
            'station.7.call',
            'station.7.program',
            'station.7.program',
            'sms.station.6',
            'call.station.6']
        topic = message_topics[random.randrange(0, len(message_topics))]
        dicked = {'this': 'that', "if": 'then', "1": 1, "2": 2}
        messagedata = json.dumps(dicked)
        print "%s %s" % (topic, messagedata)
        socket.send("%s %s" % (topic, messagedata))
        time.sleep(1)

#  Silly launch of fake daemons
#stations = db.session.query(Station).all()
#daemons = []
# for i in stations:
#    daemons.append(StationDaemon(i.id))
# test_receivers()
