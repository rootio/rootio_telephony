from config import *
import plivohelper
from time import sleep

show_host = '+256784821131'

def call(gateway, phone_number, answered):
    """
    Make a call, using (gateway, phone_number)
    TODO: actually make the other parameters correspond
    """
    print "gateway = "+gateway
    print "phone_numbers = "+phone_number
    print "answered = "+answered
    # Define Channel Variable - http://wiki.freeswitch.org/wiki/Channel_Variables
    extra_dial_string = "bridge_early_media=true,hangup_after_bridge=true"
    
    # Create a REST object
    plivo = plivohelper.REST(REST_API_URL, SID, AUTH_TOKEN, API_VERSION)
    call_params = {
        'From': '784821131', # Caller Id
        'To' : phone_number, # User Number to Call
        'Gateways' : gateway, # Gateway string to try dialing separated by comma. First in list will be tried first
        #"sofia/gateway/switch2voip/"
        #alternately, see originate sofia/gateway/GOIP/66176424223 &conference('conf_uuid-Test_Con')
        'GatewayCodecs' : "", # Codec string as needed by FS for each gateway separated by comma
        'GatewayTimeouts' : "20,20",      # Seconds to timeout in string for each gateway separated by comma
        'GatewayRetries' : "2,1", # Retry String for Gateways separated by comma, on how many times each gateway should be retried
        'ExtraDialString' : extra_dial_string,
        'AnswerUrl' : answered+'answered/',
        'HangupUrl' : answered+'hangup/',
        'RingUrl' : answered+'ringing/',
    #    'TimeLimit' : '10',
    #    'HangupOnRing': '0',
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
def bulk_call(gateway, phone_numbers, answered_URL): 
    print "gateway = "+gateway
    print "phone_numbers = "+phone_numbers
    print "answered URL= "+answered_URL

    # Define Channel Variable - http://wiki.freeswitch.org/wiki/Channel_Variables
    extra_dial_string = "bridge_early_media=true,hangup_after_bridge=true"
    
    # Create a REST object
    plivo = plivohelper.REST(REST_API_URL, SID, AUTH_TOKEN, API_VERSION)
    
    # Initiate a new outbound call using a HTTP POST
    # All parameters for bulk calls shall be separated by a delimeter
    call_params = {
        'Delimiter' : '>', # Delimter for the bulk lst
        'From': '16176424223', # Caller Id
        'To' : phone_numbers, # User Numbers to Call separated by delimeter
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
        print result
    except Exception, e:
        print e
        raise
    return [result.get('Success'),result.get('RequestUUID')]

   