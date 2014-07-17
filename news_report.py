from fluidity import StateMachine, state, transition
import plivohelper


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

from utils import call, init_logging

from zmq.eventloop import ioloop, zmqstream
ioloop.install()
#TODO: Is above just an artifact, should be in station_daemon?

import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from yapsy.IPlugin import IPlugin

logger = init_logging()

# redis is used for flagging is_master if program is across multiple stations
r = redis.StrictRedis(host='localhost', port=6379, db=0)

class News(StateMachine):
    initial_state = 'setup'

    def __init__(self, episode_id, station):
        self.caller_list = "caller_list-{0}".format(episode_id)
        self.sound_url = "{}{}{}{}".format(TELEPHONY_SERVER_IP,'/~csik/sounds/programs/',episode_id,'/current.mp3')
        self.conference = "news_report_conference-{}".format(episode_id)
        self.station = station
        self.episode_id = episode_id
        self.is_master = False
        self.fnumber = None
        super(News, self).__init__()

    def setup(self):
        logger.info("News_Report: In setup")

        #  Check if this instance should be master
        if r.get('is_master_'+str(self.episode_id)) == 'none':
            r.set('is_master_'+str(self.episode_id),self.station.id)
            self.is_master = True
            logger.info("{} is master for news report".format(str(self)))

        #check soundfile
        import requests
        response = requests.head(self.sound_url)
        if response.status_code != 200:
            logger.error('No sound file available at url:'.format(self.sound_url))

        #check to see if this is a simple outgoing gateway or a multi-line one
        top_gateway = self.station.outgoing_gateways[0]
        if top_gateway.number_top == 0:
            logger.info(str("Looks like the gateway does not need to acquire a line."))
            fnumber='3124680992' #make this a database field?
            self.fnumber=fnumber
        else:
            #allocate outgoing line
            logger.info(str(r.llen('outgoing_unused'))+" free phone lines available")
            fnumber = str(r.rpoplpush('outgoing_unused','outgoing_busy'))
            self.fnumber = fnumber
            logger.info("Allocating line {}".format(fnumber))

        #place calls
        #GATEWAY_PREFIX='951'  # This is a hack -- make this part of station or similar db field
        
        try:
            call_result = call(   to_number="{}".format(self.station.transmitter_phone.raw_number), 
                                  from_number=fnumber, 
                                  gateway=top_gateway.sofia_string, 
                                  answered='http://127.0.0.1:5000/confer/'+str(self.episode_id)+'/',
                                  #extra_dial_string="bridge_early_media=true,hangup_after_bridge=true,origination_caller_id_name=rootio,caller_name=rootio,origination_caller_id_number="+fnumber,
                                  extra_dial_string=top_gateway.extra_string,
                                )
        except Exception, e:
            logger.error('Failed to place call', exc_info=True)
            call_result = 'Error'

        if call_result !='Error':
            if call_result.get('Success') == True:
                self.RequestUUID = call_result.get('RequestUUID')
        logger.info(str(call_result))
        
        #count successful calls, 
        #if not successful, plan otherwise

        #launch show-wide listeners

    def intro(self):
        logger.info("News_Report: In intro")
        #play music
        if self.is_master == True:
            logger.info("In INTRO to news report {}".format(self.conference))
            #wait until intro music is finished


    def report(self):
        logger.info("In REPORT of news report {}".format(self.conference))
        #play report sound
        if self.is_master == True:
            self.conference
            # Create a REST object
            plivo = plivohelper.REST(REST_API_URL, SID, AUTH_TOKEN, API_VERSION)
            call_params = {'ConferenceName':'plivo', 'MemberID':'all', 'FilePath':'/home/csik/public_html/sounds/programs/3/current.mp3'}
            try:
                print plivo.conference_play(call_params)
            except Exception, e:
                print e    
                    #check on calls?
                    #
            

    def outro(self):
        logger.info("In OUTRO to news report {}".format(self.conference))
        
        #log
        #play outgoing music

    # This among all others should be "blocking", i.e. how do we assure it has 
    # executed before trying another show?


    def teardown(self):
        logger.info("In TEARDOWN of news report {}".format(self.conference))
        #hang up calls if they have not been hung up
        plivo = plivohelper.REST(REST_API_URL, SID, AUTH_TOKEN, API_VERSION)
        hangup_call_params = {'RequestUUID' : self.RequestUUID} # CallUUID for Hangup
        try:
            result = plivo.hangup_call(hangup_call_params)
            logger.info(str(result))
        except Exception, e:
            logger.error('Failed to hangup in new_report', exc_info=True)
        #clear conference

        #clear is_master semaphore
        if self.is_master == True:
            r.set('is_master_'+str(self.episode_id),'none')
        #return numbers to stack
        top_gateway = self.station.outgoing_gateways[0]
        if top_gateway>0:
            logger.info("Returning phone numbers to stack.")
            r.lrem('outgoing_busy', 0, self.fnumber) #  remove all instances for somenumber
            r.rpush('outgoing_unused', self.fnumber) #  add them back to the queue
            

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
    





