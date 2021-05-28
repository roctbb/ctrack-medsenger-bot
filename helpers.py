from datetime import datetime
from flask import request, abort
import sys
import os
from config import *

def gts():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S - ")

def log(error, terminating=False):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]


    if terminating:
        print(gts(), exc_type, fname, exc_tb.tb_lineno, error, "CRITICAL")
    else:
        print(gts(), exc_type, fname, exc_tb.tb_lineno, error)


# decorators
def verify_get(func):
    def wrapper(*args, **kargs):
        if not request.args.get('contract_id'):
            abort(422)
        if request.args.get('api_key') != API_KEY:
            abort(401)
        try:
            return func(*args, **kargs)
        except Exception as e:
            log(e, True)
            abort(500)

    wrapper.__name__ = func.__name__
    return wrapper

# decorators
def verify_json(func):
    def wrapper(*args, **kargs):
        if not request.json.get('contract_id'):
            abort(422)
        if request.json.get('api_key') != API_KEY:
            abort(401)
        try:
            return func(*args, **kargs)
        except Exception as e:
            log(e, True)
            abort(500)

    wrapper.__name__ = func.__name__
    return wrapper