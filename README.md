rootio_telephony
================

The rootio_telephony system (RTS) is a mostly internal (not outward facing) that takes care of interactions between cloud representations of stations and a) the web interface b) telephony and sms.  

At the core of RTS is the StationDaemon, one of each of which is spawned upon startup.  Each daemon reacts to messages through ZeroMQ sent from a variety of other sources, such as the telephony server or the scheduler.  It loads program representations (news, music, talk) upon command, spawns listeners and workers as necessary, coordinates recordings and votes and other program-specific activities.

In addition to the daemons, there is a Plivo & Flask app which handles connections to Freeswitch (telephony, some SMS) and Kannel (SMS).  This is relatively "dumb" in that it tries to defer to the Daemon to the degree possible, mostly handling the calls from Plivo, whereas the Daemon makes the xml requests to Plivo.

Finally, the programs themselves are state machines that initiate necessary connections and resources, run segments of programs, and "clean up" after themselves.  

This code expects a copy of rootio_web/rootio symbolically linked parallel to telephony.py.

TODO:

  Still working out separation of interests between the different components.  Should the Daemons be completely isolated from telephony code?  Where does a Daemon stop and a program begin?
  Freeswitch configuration and initiation should be handled automatically.
  Gateway or SIP system code should be abstracted; for Uganda we are using dedicated DID/DOD lines but in other cases a gsm/sip device like the GOIP would make more sense.
  SMS utils is specific to the GOIP gsm-sip device, and is a hack.

