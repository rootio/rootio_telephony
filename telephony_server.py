
from flask import Flask, request, render_template, url_for
from flask import request
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from utils import call
import utils

import sys
import os
import datetime
import requests
import time

import zmq

import plivohelper

from functools import wraps

from yapsy.PluginManager import PluginManager
import logging

from config import *


telephony_server = Flask("ResponseServer")
telephony_server.debug = True

admin = Admin(telephony_server)

telephony_server.config['SECRET_KEY'] = SECRET_KEY

# Logging
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

from rootio.extensions import db  # expects symlink of rootio in own directory
telephony_server.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(telephony_server)

from rootio.telephony.models import *
from rootio.radio.models import *

admin.add_view(ModelView(PhoneNumber, db.session))
admin.add_view(ModelView(Message, db.session))
admin.add_view(ModelView(Call, db.session))
admin.add_view(ModelView(Person, db.session))
admin.add_view(ModelView(Location, db.session))
admin.add_view(ModelView(Station, db.session))
admin.add_view(ModelView(Program, db.session))
admin.add_view(ModelView(Episode, db.session))
admin.add_view(ModelView(Role, db.session))
admin.add_view(ModelView(Gateway, db.session))

#Must send to dispatcher!
from multiprocessing import Process
from zmq.eventloop import ioloop, zmqstream
ioloop.install()

port = MESSAGE_QUEUE_PORT_TELEPHONY
context = zmq.Context()
socket = context.socket(zmq.PUB)
logger.info("Trying to bind to tcp://127.0.0.1:%s" % port)
socket.connect("tcp://127.0.0.1:%s" % port)


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance


def debug(request, url="url"): 
    logger.info( "#####ENTERING {0} #####".format(url))
    if request.method == 'POST':
        deets = request.form.items()
        logger.info(str(deets))
        method = 'POST'
    else:
        deets = ems()
        logger.info(str(deets))
        method = 'GET'
    deets = dict(deets)
    return deets


@telephony_server.errorhandler(404)
def page_not_found(error):
    """error page"""
    logger.info("404 page not found")
    return 'This URL does not exist', 404



def preload_caller(func):
    @wraps(func)
    def inner(*args, **kwargs):
        logger.info("""
            ###################################################
            #     entering function: -------->   {0}     
            ###################################################""".format(func.func_name))
        #  Separate request into a single dict called "parameters" to erase the difference between 
        #  get and post representations
        if request.method == 'POST':
            parameters = dict(request.form.items())
            parameters['request_method'] = request.method
        else:         
            parameters = dict(request.args.items())    
            parameters['request_method'] = request.method

        #  Print UUID and standardize it to uuid regardless, swap the original kwargs for our version
        try:                                                            
            if parameters.get('uuid'):
                logger.info(request.method + ", CallUUID: {0}".format(parameters['uuid']))
            else:
                logger.info(request.method + ", CallUUID: {0}".format(parameters['CallUUID']))
                parameters['uuid'] = parameters['CallUUID'] 
            # Here's where we swap the original kwargs for our version
            kwargs['parameters'] = parameters
        except Exception, e:
            logger.error('Failed to get uuid', exc_info=True)
            pass                     

        #  Handle SMS in, different from calls
        if func.func_name == 'sms_in':
            m = Message()
            m.message_uuid = parameters.get('uuid')
            m.sendtime = parameters.get('edt')
            m.text = parameters.get('body')
            m.from_phonenumber_id = get_or_create(db.session, PhoneNumber, raw_number=parameters.get('from_number'), number=parameters.get('from_number')).id
            m.to_phonenumber_id = get_or_create(db.session, PhoneNumber, raw_number=parameters.get('fr'), number=parameters.get('fr')).id         
            logger.info("about to commit {}".format(str(m.__dict__)))
            db.session.add(m)
            db.session.commit()      
            kwargs['parameters']['Message_object_id'] = m.id
        else:
            #todo, add fields to model for different call stages and times, like ringing, etc.
            #TODO sent a message to a logger daemon rather than logging this directly, but perhaps increment a variable
            #TODO no need to use get_or_create for anything but ringing
            if parameters.get('CallStatus') == 'ringing':
                c = get_or_create(db.session, Call, call_uuid=parameters.get('CallUUID'))
                c.call_uuid = parameters.get('CallUUID')
                c.start_time = datetime.now()                                                                     
                c.from_phonenumber_id = get_or_create(db.session, PhoneNumber, raw_number=parameters.get('From'), number=parameters.get('From')).id
                c.to_phonenumber_id = get_or_create(db.session, PhoneNumber, raw_number=parameters.get('To'), number=parameters.get('To')).id      
                logger.info("about to commit {}".format(str(c.__dict__)))
                db.session.add(c)
                db.session.commit()
                kwargs['parameters']['Call_object_id'] = c.id
            if parameters.get('CallStatus') == 'completed':
                c = get_or_create(db.session, Call, call_uuid=parameters.get('CallUUID'))
                kwargs['parameters']['Call_object_id'] = c.id
            if parameters.get('CallStatus') == 'completed':
                c = get_or_create(db.session, Call, call_uuid=parameters.get('CallUUID'))
                c.end_time = datetime.now()                                                                     
                logger.info("about to commit {}".format(str(c.__dict__)))   
                db.session.add(c)   
                db.session.commit()       
        logger.info("Returning Parameters = {}".format(str(kwargs['parameters'])))      
        return func(*args, **kwargs)
    return inner
        
        
@telephony_server.route('/sms/in', methods=['GET', 'POST'])   
@preload_caller
def sms_in(parameters):
    """Receive an sms
    { 'uuid': uuid, 
      'edt': edt, 
      'fr': fr, 
      'to': to, 
      'from_number': from_number, 
      'body': body,
    } 
    """
    logger.info("Parameters =" + str(parameters))    
    logger.info("We received an SMS")      
    logger.info(parameters['from_number'])
    logger.info(str(parameters['from_number']) == SHOW_HOST)                
    #look at conferenceplay
    #if parameters['from_number'] == SHOW_HOST or parameters['from_number'] == SHOW_HOST[2:]:     
    #    answered_url = "http://127.0.0.1:5000/answered/"
    #    utils.call("sofia/gateway/switch2voip/",parameters['from_number'], answered_url) 
    #else:  #obviously the below would only happen with approval of host
    #    answered_url = "http://127.0.0.1:5000/answered/"
    #    utils.call("sofia/gateway/switch2voip/",parameters['from_number'], answered_url)       
    return "OK"


@telephony_server.route('/waitmusic/', methods=['GET', 'POST'])
def waitmusic():
    if request.method == 'POST':
        logger.info(str(request.form.items()))
    else:
        logger.info(str(request.args.items()))
    
    r = plivohelper.Response()     
    r.addPlay("/home/csik/public_html/sounds/programs/3/current.mp3")
    logger.info("RESTXML Response => {}".format(r))
    #return render_template('response_template.xml', response=r)    
    return "OK"


@telephony_server.route('/hostwait/', methods=['GET', 'POST'])
def hostwait():
    if request.method == 'POST':
        logger.info(str(request.form.items()))
    else:
        logger.info(str(request.args.items()))
    r = plivohelper.Response()
    r.addPlay(TELEPHONY_SERVER_IP+"/~csik/sounds/english/Hello_Host.mp3")
    r.addPlay(TELEPHONY_SERVER_IP+"/~csik/sounds/english/You_Have_X_Listeners.mp3")
    r.addPlay(TELEPHONY_SERVER_IP+"/~csik/sounds/english/Instructions.mp3")
    logger.info("RESTXML Response => {}".format(r))
    return render_template('response_template.xml', response=r)


#@telephony_server.route('/answered/', methods=['GET', 'POST'])
#@preload_caller 
#def answered(parameters):
#    # Post params- 'CallUUID': unique id of call, 'Direction': direction of call,
#    #               'To': Number which was called, 'From': calling number,
#    #               If Direction is outbound then 2 additional params:
#    #               'ALegUUID': Unique Id for first leg,
#    #               'ALegRequestUUID': request id given at the time of api call
#                                                                          
#    r = plivohelper.Response() 
#    from_number = parameters.get('From')
#    logger.info(SHOW_HOST)
#    logger.info("Match Host: " + str(str(parameters['From']) == SHOW_HOST or str(parameters['From']) == SHOW_HOST[2:]))               
#    if str(parameters['From']) == SHOW_HOST or str(parameters['From']) == SHOW_HOST[2:] :     
#        p = r.addConference("plivo", muted=False, 
#                            enterSound="beep:2", exitSound="beep:1",
#                            startConferenceOnEnter=True, endConferenceOnExit=True,
#                            waitSound = ANSWERED+'hostwait/',
#                            timeLimit = 0, hangupOnStar=True)
#    else:
#        p = r.addConference("plivo", muted=False, 
#                            enterSound="beep:2", exitSound="beep:1",
#                            startConferenceOnEnter=True, endConferenceOnExit=False,
#                            waitSound = ANSWERED+'waitmusic/',
#                            timeLimit = 0, hangupOnStar=True)
#    logger.info("RESTXML Response => {}".format(r))
#    return render_template('response_template.xml', response=r)

@telephony_server.route('/confer/<schedule_program_id>/<action>/', methods=['GET', 'POST'])
@preload_caller 
def confer(parameters, schedule_program_id, action):
    # Post params- 'CallUUID': unique id of call, 'Direction': direction of call,
    #               'To': Number which was called, 'From': calling number,
    #               If Direction is outbound then 2 additional params:
    #               'ALegUUID': Unique Id for first leg,
    #               'ALegRequestUUID': request id given at the time of api call

    if action == "ringing":
        logger.info("Ringing for scheduled_program {}".format(schedule_program_id))
        return "OK"
    elif action == "heartbeat":
        logger.info("Heartbeat for scheduled_program {}".format(schedule_program_id))
        return "OK"
    elif action == "hangup":
        # THIS IS WHERE NUMBER IS TRANSFERRED FROM outgoing_busy TO outgoing_unused
        logger.info("Hangup for scheduled_program {}".format(schedule_program_id))
        return "OK"
    elif action == "answered":
        #  This is where station daemons are contacted
        r = plivohelper.Response() 
        from_number = parameters.get('From')
        try:
            logger.info("url_for format = {}".format(url_for('confer_events')))
        except Exception:
            logger.info("unable to get url_for")
        p = r.addConference("plivo", 
                            muted=False, 
                            enterSound="beep:2", 
                            exitSound="beep:1",
                            startConferenceOnEnter=True, 
                            endConferenceOnExit=False,
                            waitSound = ANSWERED+'waitmusic/',
                            timeLimit = 0, 
                            hangupOnStar=True,
                            callbackUrl=ANSWERED+'confer_events/', 
                            callbackMethod="POST", 
                            digitsMatch="#9,#7,#8,7,8,9",
                            )
        logger.info("RESTXML Response => {}".format(r))
        return render_template('response_template.xml', response=r)
    else:
        logger.info("Could not recognize plivo url variable")
        return "OK"

@telephony_server.route('/confer_events/', methods=['POST'])
@preload_caller 
def confer_events(parameters):       
    if parameters.get('ConferenceDigitsMatch'):
        logger.info("Received a digit in conference:{}".format(parameters.get('ConferenceDigitsMatch')))
    return "OK"


#  This function should pretty much only be invoked for unsolicited calls 

@telephony_server.route('/answered/', methods=['GET', 'POST'])
@telephony_server.route('/ringing/', methods=['GET', 'POST'])
@telephony_server.route('/heartbeat/', methods=['GET', 'POST'])
@telephony_server.route('/hangup/', methods=['GET', 'POST'])
@preload_caller 
def root(parameters):
    logger.info("Request.path:{}".format(request.path))
    debug(request, "root")
    
    if request.path == "/heartbeat/":
        logger.info("Heartbeat for call from {0} to {1}".format(parameters.get('From'), parameters.get('To')))
        return "OK"
    elif parameters.get('CallStatus') == "completed":
        logger.info("Hangup of call from {0} to {1}".format(parameters.get('From'), parameters.get('To')))
        return "OK"
    elif request.path == "/answered/":
        if parameters.get('CallStatus') == "ringing":
            #Check to see if incoming call is TO a station's cloud number -- the public number of the station
            phone_id = db.session.query(PhoneNumber).filter(PhoneNumber.raw_number==parameters.get('To')).one().id
            station = db.session.query(Station).filter(Station.cloud_phone_id==phone_id).first()
            if station:
                logger.info("Received call from cloud number:")
                logger.info("Station: {}, Number:{}".format(station.name, station.cloud_phone.raw_number))
                logger.info("Choosing to not answer")
                #should send to relevant station now....
                topic = "station.{}.call".format(station.id)
                from_id = db.session.query(PhoneNumber).filter(PhoneNumber.raw_number==parameters.get('From')).one().id
                messagedata =   {
                                    "type":"call", 
                                    "from":parameters.get('From'),
                                    "from_id":from_id.id,
                                    "time":parameters.get('start_time'),
                                }
                #send this to Josh's dispatcher 
                socket.send("%s %s" % (topic, messagedata))
                logger.info("Session name = {}".format(session.get('name')))
                time.sleep(5),
                return "OK"
            else:
                logger.info("Received call from non-cloud number")
                return "OK"
            logger.info("Ringing call from {0} to {1}".format(parameters.get('From'), parameters.get('To')))

        #  Not ringing means it is answered    
        else:    
        #  This is where station daemons are contacted
            r = plivohelper.Response() 
            from_number = parameters.get('From')
            p = r.addConference("plivo", muted=False, 
                                enterSound="beep:2", exitSound="beep:1",
                                startConferenceOnEnter=True, endConferenceOnExit=False,
                                waitSound = ANSWERED+'waitmusic/',
                                timeLimit = 0, hangupOnStar=True)
            logger.info("RESTXML Response => {}".format(r))
            return render_template('response_template.xml', response=r)
    else:
        logger.info("Could not recognize plivo url variable")
        return "OK"

def main():
    plugins()
    return

def plugins():   
    # Load the plugins from the plugin directory.
    manager = PluginManager()
    manager.setPluginPlaces(["plugins"])
    manager.collectPlugins()

    # Loop round the plugins and print their names.
    for p in manager.getAllPlugins():
        p.plugin_object.print_name()
        p.plugin_object.activate()


if __name__ == '__main__':
    if not os.path.isfile("templates/response_template.xml"):
        logger.info("Error : Can't find the XML template : templates/response_template.xml")
    else:
        telephony_server.run(host='127.0.0.1', port=5000)

