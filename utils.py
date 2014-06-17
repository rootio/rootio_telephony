from config import *
import plivohelper
from time import sleep


ANSWERED = 'http://127.0.0.1:5000/'  
SOUNDS_ROOT = 'http://176.58.125.166/~csik/sounds/'
EXTRA_DIAL_STRING = "bridge_early_media=true,hangup_after_bridge=true"

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


def call(to_number, from_number, gateway, answered=ANSWERED,extra_dial_string=EXTRA_DIAL_STRING):
    """
    Make a call, using (gateway, phone_number)
    TODO: actually make the other parameters correspond
    """
    logger.info("gateway = "+gateway)
    logger.info("from {0}, to {1}".format(from_number, to_number))
    logger.info("answered = "+answered)
    # Define Channel Variable - http://wiki.freeswitch.org/wiki/Channel_Variables

    # Create a REST object
    plivo = plivohelper.REST(REST_API_URL, SID, AUTH_TOKEN, API_VERSION)
    call_params = {
        'From': from_number, # Caller Id
        'To' : to_number, # User Number to Call
        'Gateways' : gateway, # Gateway string to try dialing separated by comma. First in list will be tried first
        'GatewayCodecs' : "", # Codec string as needed by FS for each gateway separated by comma
        'GatewayTimeouts' : "20,20",      # Seconds to timeout in string for each gateway separated by comma
        'GatewayRetries' : "2,1", # Retry String for Gateways separated by comma, on how many times each gateway should be retried
        'ExtraDialString' : extra_dial_string,
        'AnswerUrl' : answered+'answered/',
        'HangupUrl' : answered+'hangup/',
        'RingUrl' : answered+'ringing/',
        #'TimeLimit' : '15',
    	#'HangupOnRing': '0',
    }
    request_uuid = ""

    #Perform the Call on the Rest API
    try:
        result = plivo.call(call_params)
        logger.info(str(result))
        return result
    except Exception, e:
        logger.error('Failed to make utils.call', exc_info=True)
        pass
    return "Error"
    
#   ONLY CONNECTS FIRST SUCCESSFUL CONNECTION
def group_call(gateway, phone_numbers, answered): 
    print "gateway = "+gateway
    print "phone_numbers = "+phone_numbers
    print "answered = "+answered

    # Define Channel Variable - http://wiki.freeswitch.org/wiki/Channel_Variables
    extra_dial_string = "bridge_early_media=true,hangup_after_bridge=true"
    
    # Create a REST object
    plivo = plivohelper.REST(REST_API_URL, SID, AUTH_TOKEN, API_VERSION)
    
    # Initiate a new outbound call to user/1000 using a HTTP POST
    # All parameters for bulk calls shall be separated by a delimeter
    call_params = {
        'Delimiter' : '>', # Delimter for the bulk list
        'From': SHOW_HOST, # Caller Id
        'To' : phone_numbers, # User Numbers to Call separated by delimeter
        'Gateways' : gateway, # Gateway string for each number separated by delimeter
        'GatewayCodecs' : "", # Codec string as needed by FS for each gateway separated by delimeter
        'GatewayTimeouts' : "20>20", # Seconds to timeout in string for each gateway separated by delimeter
        'GatewayRetries' : "2>1", # Retry String for Gateways separated by delimeter, on how many times each gateway should be retried
        'ExtraDialString' : extra_dial_string,
        'AnswerUrl' : answered+'answered/',
        'HangupUrl' : answered+'hangup/',
        'RingUrl' : answered+'ringing/',
    #    'ConfirmSound' : "test.wav",
    #    'ConfirmKey' : "1",
    #    'RejectCauses': 'NO_USER_RESPONSE,NO_ANSWER,CALL_REJECTED,USER_NOT_REGISTERED',
    #    'ConfirmSound': '/usr/local/freeswitch/sounds/en/us/callie/ivr/8000/ivr-requested_wakeup_call_for.wav',
    #    'ConfirmKey': '9'
    #    'TimeLimit' : '10>30',
    #    'HangupOnRing': '0>0',
    }

    request_uuid = ""

    #Perform the Call on the Rest API
    try:
        result = plivo.call(call_params)
        print result
    except Exception, e:
        print e
        raise
    return [result.get('Success'),result.get('RequestUUID')]


#   CONNECTS MULTIPLES
def bulk_call(to_numbers, from_number, gateway, answered=ANSWERED,extra_dial_string=EXTRA_DIAL_STRING): 

    # Create a REST object
    plivo = plivohelper.REST(REST_API_URL, SID, AUTH_TOKEN, API_VERSION)
    
    # Initiate a new outbound call using a HTTP POST
    # All parameters for bulk calls shall be separated by a delimeter
    call_params = {
        'Delimiter' : '>', # Delimter for the bulk lst
        'From': from_number, # Caller Id
        'To' : to_numbers, # User Numbers to Call separated by delimeter
        'Gateways' : gateway, # Gateway string for each number separated by delimeter
        'GatewayCodecs' : "", # Codec string as needed by FS for each gateway separated by delimeter
        'GatewayTimeouts' : "20>20", # Seconds to timeout in string for each gateway separated by delimeter
        'GatewayRetries' : "2>1", # Retry String for Gateways separated by delimeter, on how many times each gateway should be retried
        'ExtraDialString' : extra_dial_string,
        'AnswerUrl' : answered_URL+'answered/',
        'HangupUrl' : answered_URL+'hangup/',
        'RingUrl' : answered_URL+'ringing/',
    #    'ConfirmSound' : "test.wav",
    #    'ConfirmKey' : "1",
    #    'RejectCauses': 'NO_USER_RESPONSE,NO_ANSWER,CALL_REJECTED,USER_NOT_REGISTERED',
    #    'ConfirmSound': '/usr/local/freeswitch/sounds/en/us/callie/ivr/8000/ivr-requested_wakeup_call_for.wav',
    #    'ConfirmKey': '9'
    #    'TimeLimit' : '10>30',
    #    'HangupOnRing': '0>0',
    }

    request_uuid = ""

    #Perform the Call on the Rest API
    try:
        result = plivo.bulk_call(call_params)
        logger.info(str(result))
        return [result.get('Success'),result.get('RequestUUID')]
    except Exception, e:
        logger.error('Failed to make utils.bulkcall', exc_info=True)
        pass
    return "Error"   
