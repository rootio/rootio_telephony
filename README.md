rootio_telephony
================

The rootio_telephony server is a mostly internal (not outward facing) that interfaces between telephony hardware and rootio_web.  It takes and makes calls and sms messages, routing appropriately based on program state machines.  It interacts with Plivo & Freeswitch, which in turn interact with either a sim box, SIP DID/DOD endpoints, a raspbx or similar gsm to sip systems.

SMS utils is specific to the GOIP gsm-sip device, and is frankly a bit of a hack.

This code expects a copy of rootio_web/rootio symbolically linked parallel to telephony.py.