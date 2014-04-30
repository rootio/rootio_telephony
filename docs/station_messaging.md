zeromq topics
    dot separated, with a nested hierarchy

initial topics:
    station.<ID>.program
        publisher: rootio_web
        subscriber: rootio_telephony
        payload: {'episode_id':'',
                  'onair_episode_id':''
                  'starts_at':iso datetime,
        }

    station.<ID>.sms
        publisher: plivo
        subscriber: rootio_telephony
        payload: csik to define

    station.<ID>.call
        publisher: plivo
        subscriber: rootio_telephony
        payload: csik to define

    station.<ID>.db
        publisher: rootio_web
        subscriber: rootio_telephony
        payload: {'field':string, field name to to be updated,
                  'value':new value}

    emergency.<station_ID>
        publisher: rootio_web,
        subscriber: rootio_telephony,
        payload: {'affects':station_id_list, #if not prefixed by
                  'message':'This is a test of the emergency broadcast system'} 
