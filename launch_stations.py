from config import *

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from rootio.extensions import db

import zmq
from utils import ZMQ, init_logging

from rootio.telephony.models import *
from rootio.radio.models import *

import time
app = Flask("ResponseServer")
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)

logger = init_logging('launch_stations')

daemons = []
from station_daemon import StationDaemon
stations = db.session.query(Station).all()
for i in stations:
        daemons.append(StationDaemon(i.id))
time.sleep(1)

