
from flask.ext.script import Manager, Shell

from telephony_server import telephony_server,db

def _make_context():
    import rootio.telephony.models
    import rootio.radio.models
    return dict(db=db, t_models=rootio.telephony.models, r_models=rootio.radio.models)

manager = Manager(telephony_server)
manager.add_command("sh", Shell(make_context=_make_context))


from rootio.extensions import db
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy(telephony_server)
from rootio.telephony.models import *
from rootio.radio.models import *
from rootio.user.models import *

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
