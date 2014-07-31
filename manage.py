
from flask.ext.script import Manager, Shell
from telephony_server import telephony_server,db

def _make_context():
    import rootio.telephony.models
    import rootio.radio.models
    import rootio.user.models
    return dict(db=db, u=rootio.user.models, t=rootio.telephony.models, r=rootio.radio.models)

from config import *
manager = Manager(telephony_server)
manager.add_command("sh", Shell(make_context=_make_context))

from rootio.extensions import db
from flask.ext.sqlalchemy import SQLAlchemy
telephony_server.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(telephony_server)

from rootio.telephony.models import *
from rootio.radio.models import *
from rootio.user.models import *

@manager.command
def hello():
    print "hello"

@manager.command
def createdb():
    import rootio.telephony.models
    import rootio.radio.models
    import rootio.user.models
    db.create_all()
    _make_context()
    admin = User(
        name=u'admin2',
        email=u'admin2@example.com',
        password=u'123456',
        role_code=ADMIN,
        status_code=1,
        user_detail=UserDetail(
            gender_code=1,
            age=25,
            url=u'http://example.com',
            location=u'Kampala',
            bio=u'')
        )
    db.session.add(admin)
    db.session.commit()


@manager.command
def reloaddb():    
    db_session.remove()
    db.drop_all()
    from rootio.telephony.models import PhoneNumber, Message
    db.create_all()



if __name__ == "__main__":
    manager.run()
