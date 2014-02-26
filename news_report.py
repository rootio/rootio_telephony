from fluidity import StateMachine, state, transition

"""
Sketch of news show.  

At most basic, the show consists of making outgoing calls and playing a news report.

Options:
	Have news report read live from a location
	Have a live reporter reading texts at the end
	Have a regional segment following the national
	Advertisements in-line

"""
import zmq
from config import *
import redis

from utils import call

from zmq.eventloop import ioloop, zmqstream
ioloop.install()

import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from yapsy.IPlugin import IPlugin

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


#  code for two-way clienting
#SUB_PORT = MESSAGE_QUEUE_PORT  #  This has to be sent in the initial message
#context = zmq.Context()
#socket = context.socket(zmq.PAIR)
#socket.connect("tcp://localhost:%s" % port)
#socket.send(response)

# Use redis lists for atomic access to a list of available numbers
# redis lists
#r.rpush('ttt','666')
#r.rpush('ttt','77')
#r.lrange('ttt',0,-1)
#new_number = r.brpoplpush('ttt','rrr')
#r.llen('outgoing_unused')

#somenumber = '0417744888'
#r.lrem('outgoing_busy', 0, somenumber) #  remove all instances for somenumber
#r.rpush('outgoing_unused', somenumber) #  add them back to the queue


class News(StateMachine):
	initial_state = 'setup'

	def __init__(self, episode_id, station):
		self.caller_list = "{0}-{1}".format('caller_list',episode_id)
		self.sound_url = "{}{}{}{}".format(TELEPHONY_SERVER_IP,'/~csik/sounds/programs/',episode_id,'/current.mp3')
		self.conference = "news_report_conference-{}".format(episode_id)
		self.station = station
		self.episode_id = episode_id
		super(News, self).__init__()
        

	def setup(self):
		logger.info("News_Report: In setup")

		#  Start caller/messager list
		r = redis.StrictRedis(host='localhost', port=6379, db=0)
		r.set(self.caller_list,[])
		# from now on get list as 
		#numbers = ast.literal_eval(r.get(self.caller_list))
		#numbers.append(incoming)	
		#r.set(self.caller_list,numbers)

		#check soundfile
		import requests
		response = requests.head(self.sound_url)
		if response.status_code != 200:
			logger.error('No sound file available at url:'.format(self.sound_url))

		#allocate outgoing line
		logger.info(str(r.llen('outgoing_unused'))+" free phone lines available")
		number = r.rpoplpush('outgoing_unused','outgoing_busy')

		#place calls
		call_result = call(   to_number=self.station.cloud_phone.raw_number, 
        					  from_number=number, 
        					  gateway='sofia/gateway/utl/', 
        					  answered='http://127.0.0.1:5000/'+'/confer/'+str(self.episode_id)+'/',
        					  extra_dial_string="bridge_early_media=true,hangup_after_bridge=true,origination_caller_id_name=rootio,origination_caller_id_number="+number,
    						)

		logger.info(str(call_result))
		#count successful calls, plan otherwise
		#launch show-wide listeners -- or does station do that?


	def intro(self):
		logger.info("News_Report: In intro")
		#wait until intro music is finished
		#play sound to conference
		#check progress of sound file

	def report(self):
		logger.info("News_Report: In report")
		#play report sound
		#check on calls?
		#
	def outro(self):
		logger.info("News_Report: In outro")
		#hang up calls 
		#log
		#play outgoing music

	# This among all others should be "blocking", i.e. how do we assure it has 
	# executed before trying another show?
	def teardown(self):
		logger.info("News_Report: In teardown")
		#hang up calls if they have not been humg up
		#clear conference


	#  Set up states
	state('setup',enter=setup)
	state('intro',enter=intro)
	state('report',enter=report)
	state('outro',enter=outro)
	state('teardown',enter=teardown)
	#  Set up transitions, note they expect serial progression except for teardown
	transition(from_='setup', event='go_intro', to='intro')
	transition(from_='intro', event='go_report', to='report')
	transition(from_='report', event='go_outro', to='outro')
	transition(from_=['outro','report','intro','setup'], event='go_teardown', to='teardown')
	





