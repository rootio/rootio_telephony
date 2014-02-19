
from flask import Flask, request, render_template
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


import plivohelper

from functools import wraps

from yapsy.PluginManager import PluginManager
import logging

from config import *

telephony_server = Flask("ResponseServer")
telephony_server.debug = True

admin = Admin(telephony_server)


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

SHOW_HOST = '16176424223'
ANSWERED = 'http://127.0.0.1:5000/'  
SOUNDS = 'http://176.58.125.166/~csik/sounds/swahili/'     

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
        deets = request.args.items()
        logger.info(str(deets))
        method = 'GET'
    deets = dict(deets)
    return deets


@telephony_server.errorhandler(404)
def page_not_found(error):
    """error page"""
    logger.info("404 page not found")
    return 'This URL does not exist', 404


@telephony_server.route('/ringing/', methods=['GET', 'POST'])
def ringing():
    """ringing URL"""
    # Post params- 'to': ringing number,
    # request_uuid': request id given at the time of api call
    logger.info("We got a ringing notification")
    return "OK"


@telephony_server.route('/hangup/', methods=['GET', 'POST'])
def hangup():
    """hangup URL"""
    # Post params- 'request_uuid': request id given at the time of api call,
    #               'CallUUID': unique id of call, 'reason': reason of hangup
    logger.info("We got a hangup notification")
    c = Call()

    return "OK"


@telephony_server.route('/heartbeat/', methods=['GET', 'POST'])
def heartbeat():
    """Call Heartbeat URL"""
    logger.info("We got a call heartbeat notification\n")

    if request.method == 'POST':
        print request.form
    else:
        print request.args
    return "OK"


def preload_caller(func):
    @wraps(func)
    def inner(*args, **kwargs):
        logger.info("""###################################################
            #     entering function: ---------------> {0}     #
            ###################################################""".format(func.func_name))
        if request.method == 'POST':
            parameters = dict(request.form.items())
        else:         
            parameters = dict(request.args.items())    
        try:                                                            
            if parameters.get('uuid'):
                logger.info(request.method + ", CallUUID: {0}".format(parameters['uuid']))
            else:
                logger.info(request.method + ", CallUUID: {0}".format(parameters['CallUUID']))
            logger.info("Parameters = {}".format(str(parameters)))  
            kwargs['parameters'] = parameters
        except Exception, e:
            logger.error('Failed to get uuid', exc_info=True)
            pass                     
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
        else:
            #todo, add fields to model for different call stages and times, like ringing, etc.
            if parameters.get('CallStatus') == 'ringing':
                c = get_or_create(db.session, Call, call_uuid=parameters.get('CallUUID'))
                c.call_uuid = parameters.get('CallUUID')
                c.start_time = datetime.datetime.now()                                                                     
                c.from_phonenumber_id = get_or_create(db.session, PhoneNumber, raw_number=parameters.get('From'), number=parameters.get('From')).id
                c.to_phonenumber_id = get_or_create(db.session, PhoneNumber, raw_number=parameters.get('To'), number=parameters.get('To')).id      
                logger.info("about to commit {}".format(str(c.__dict__)))
                db.session.add(c)
                db.session.commit()
            if parameters.get('CallStatus') == 'completed':
                c = get_or_create(db.session, Call, call_uuid=parameters.get('CallUUID'))
                c.end_time = datetime.datetime.now()                                                                     
                logger.info("about to commit {}".format(str(m.__dict__)))   
                db.session.add(c)   
                db.session.commit()            
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
    #r.addSpeak('Your mama is so fat.')
    #r.addSpeak("Your father was a hampster and your mother smelt of elderberries.")
    r.addPlay("/usr/local/freeswitch/sounds/en/us/callie/ivr/8000/ivr-welcome.wav")
    r.addPlay("/usr/local/freeswitch/sounds/music/8000/suite-espanola-op-47-leyenda.wav")
    logger.info("RESTXML Response => {}".format(r))
    return render_template('response_template.xml', response=r)    


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


@telephony_server.route('/answered/', methods=['GET', 'POST'])
@preload_caller 
def answered(parameters):
    # Post params- 'CallUUID': unique id of call, 'Direction': direction of call,
    #               'To': Number which was called, 'From': calling number,
    #               If Direction is outbound then 2 additional params:
    #               'ALegUUID': Unique Id for first leg,
    #               'ALegRequestUUID': request id given at the time of api call
                                                                          
    r = plivohelper.Response() 
    from_number = parameters.get('From')
    logger.info(SHOW_HOST)
    logger.info("Match Host: " + str(str(parameters['From']) == SHOW_HOST or str(parameters['From']) == SHOW_HOST[2:]))               
    if str(parameters['From']) == SHOW_HOST or str(parameters['From']) == SHOW_HOST[2:] :     
        p = r.addConference("plivo", muted=False, 
                            enterSound="beep:2", exitSound="beep:1",
                            startConferenceOnEnter=True, endConferenceOnExit=True,
                            waitSound = ANSWERED+'hostwait/',
                            timeLimit = 0, hangupOnStar=True)
    else:
        p = r.addConference("plivo", muted=False, 
                            enterSound="beep:2", exitSound="beep:1",
                            startConferenceOnEnter=True, endConferenceOnExit=False,
                            waitSound = ANSWERED+'waitmusic/',
                            timeLimit = 0, hangupOnStar=True)
    logger.info("RESTXML Response => {}".format(r))
    return render_template('response_template.xml', response=r)

@telephony_server.route('/confer/<station_id>/<program_id>/<episode_id>', methods=['GET', 'POST'])
@preload_caller 
def confer(parameters):
    # Post params- 'CallUUID': unique id of call, 'Direction': direction of call,
    #               'To': Number which was called, 'From': calling number,
    #               If Direction is outbound then 2 additional params:
    #               'ALegUUID': Unique Id for first leg,
    #               'ALegRequestUUID': request id given at the time of api call
                                                                          
    r = plivohelper.Response() 
    from_number = parameters.get('From')
    logger.info(SHOW_HOST)
    logger.info("Match Host: " + str(str(parameters['From']) == SHOW_HOST or str(parameters['From']) == SHOW_HOST[2:]))               
    if str(parameters['From']) == SHOW_HOST or str(parameters['From']) == SHOW_HOST[2:] :     
        p = r.addConference("plivo", muted=False, 
                            enterSound="beep:2", exitSound="beep:1",
                            startConferenceOnEnter=True, endConferenceOnExit=True,
                            waitSound = ANSWERED+'hostwait/',
                            timeLimit = 0, hangupOnStar=True)
    else:
        p = r.addConference("plivo", muted=False, 
                            enterSound="beep:2", exitSound="beep:1",
                            startConferenceOnEnter=True, endConferenceOnExit=False,
                            waitSound = ANSWERED+'waitmusic/',
                            timeLimit = 0, hangupOnStar=True)
    logger.info("RESTXML Response => {}".format(r))
    return render_template('response_template.xml', response=r)




def main():
    plugins()
    return

def plugins():   
    # Load the plugins from the plugin directory.
    manager = PluginManager()
    manager.setPluginPlaces(["plugins"])
    manager.collectPlugins()

    # Loop round the plugins and print their names.
    for plugin in manager.getAllPlugins():
        plugin.plugin_object.print_name()
    p = manager.getAllPlugins()[0]
    p.plugin_object.activate()


if __name__ == '__main__':
    if not os.path.isfile("templates/response_template.xml"):
        logger.info("Error : Can't find the XML template : templates/response_template.xml")
    else:
        telephony_server.run(host='127.0.0.1', port=5000)

