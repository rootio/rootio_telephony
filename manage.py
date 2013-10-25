
from flask.ext.script import Manager

from telephony_server import telephony_server,db

manager = Manager(telephony_server)     

from rootio.extensions import db
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy(telephony_server)
from rootio.telephony.models import *
from rootio.radio.models import *

@manager.command
def hello():
    print "hello"

@manager.command
def createdb():
    db.create_all()

@manager.command
def reloaddb():    
    db.drop_all()
    from rootio.telephony.models import PhoneNumber, Message
    db.create_all()


if __name__ == "__main__":
    manager.run()
