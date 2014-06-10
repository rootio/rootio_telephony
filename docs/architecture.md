RootIO Telephony
================

The RootIO telephony subsystem has grown to encompass more than just
telephony.  Currently it houses:
1) The Telephony Server, which is Plivo/flask app that runs locally
on the server using the flask wsgi debug server.  This takes/makes
requests to freeswitch, enabling sending and receiving of calls.  The
smsutils subsection handles sending/receiving sms.
2) The Station Daemon, which is a separate python program that creates n
station objects that have zeromq listeners.  These load programs, and
together with the program should be able to handle high-level telephony
features and media, interactions with the database, etc.
3) Programs, which are loaded/unloaded by the Station as per the
scheduler.  

Telephony Server
----------------
Unlike the Plivo example documents, the telephony server does not have a
lot of code in its functions; the goal is to handle incoming calls, do
anything necessary to immediately deal with telephony requirements, but
then dispatch the call information to the station, which in turn refers 
to the program to figure out how to handle it.  Thus the goal is to have 
the bulk of the conditional logic elsewhere.

Key to understanding Plivo (and Freeswitch underneath) is that there are two
main modes in telephony, receiving (and processing) calls, and
initiating actions.  Receiving and processing calls -- essentially the
asyncronous part -- is handled through Plivo's xml library, much like
web requests.  This is the bulk of what the Telephony Server does.
Initiating actions happens through Plivo's REST API, and this is done
primarily by stations and programs. 

Station Daemon
--------------
The Daemon spins off a set of station instances into ram, which interact
with the scheduler, database, and other applications. The scheduler
should be able to load and unload programs, and handle longer running
processes like analyzing the station phone over 

Program
-------
The program is a state machine with a set of specific modes.  These
might be a setup mode, which ensures that resources are available and
loaded, an intro mode, an interactive IVR mode with a live dj, and 
finally teardown.  Each program has access to
the system (for now) and is just a regular python file.  While
eventually we would love for it to be a json description of higher level
functionality, for now it is first-class code.  To be honest, we have
yet to draw a fine line between where the program starts and stops and
where the station begins, but it should be fairly clear in practice.

Example
-------
A live news report is about to begin.  There are 27 stations
subscribed to that report.  The scheduler tells all 27 stations to
load the news report; the first station to be created grabs the "master"
token.  Each station initiates the outgoing call to its station phone with 
Plivo, additionally passing Plivo the url for "confer."  When the calls
successfully connect, the telephony server receives a request for confer
with a station id.  It patches each call into the conference, and
notifies the respective station of success.  The master station then starts to play
media, etc. into the conference.  When the media is over, the station
daemons initiate hangups; the telephony server is notified on hangups
and tells the stations when they have happened.

