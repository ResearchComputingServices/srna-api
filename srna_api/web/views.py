from flask import request, jsonify, url_for, Blueprint
from flask import json, jsonify, Response, blueprints
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
from srna_api.decorators.authentication import authentication
import srna_api.web.role_view
import srna_api.web.user_view
import srna_api.web.image_view
import srna_api.web.user_field_type_view
import srna_api.web.user_field_category_view
import srna_api.web.enumeration_view
import srna_api.web.user_keycloak
import srna_api.web.authorization_view
from celery import Celery
#from srna_api.srna_factory import celery
#from app import app
import os
import random
import time
from srna_api.srna_factory import make_celery
from srna_api.extensions import app

celery = make_celery(app)

@celery.task()
def add_together(a, b):
    print("\nAdd\n")
    return a + b

@celery.task(bind=True)
def long_task(self):
    print("\nlong_task processing\n")
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

@srna_bp.route("/", methods=['GET'])
@crossdomain(origin='*')
@authentication
def hello():
    return "Hello Language2Test!"

@srna_bp.route('/longtask', methods=['POST'])
@crossdomain(origin='*')
@authentication
def longtask():
    result = add_together.delay(23, 42)
    result.wait()  # 65
    return jsonify({}), 202, {}

@srna_bp.route('/status/<task_id>')
@crossdomain(origin='*')
@authentication
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)