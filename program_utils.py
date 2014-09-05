"""Program Utilities
    Tools available to programs
"""

from datetime import datetime, timedelta


def get_redis_connection():
    """Pass a redis url and receive an active redis object -- should be called once on program creation.
    """
    pass

def is_master():
    """Pass a redis url and one's own info, and receive a boolean.  Should check for type of passed url to make sure it is redis, allowing other mechanisms in the future.
    State of mastery should be kept in program object from then on.
    """
    pass

def sleep_advance_on_wake(scheduler, sleep_time, wake_function):
    execdate = datetime.now()+timedelta(seconds=sleep_time)
    print "Function = {}".format(wake_function)
    job = scheduler.add_date_job(wake_function,execdate)
    return job


def connect_caller():
    pass


def disconnect_caller():
    pass


def get_number_of_waiting_callers():
    pass


def play_message():
    pass

#these should be station functions, no?
def call_transmitter():
    pass


def disconnect_transmitter():
    pass



def make_self_master():
    pass
