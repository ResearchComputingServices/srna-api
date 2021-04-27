from flask import request, jsonify, url_for, Blueprint
from flask import json, jsonify, Response, blueprints
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
import srna_api.web.srna_view
from celery import Celery
import time
from srna_api.extensions import celery

@celery.task()
def add_together(a, b):
    time.sleep(10)
    print("\nCompleted add_together after 10 seconds delay\n")
    return a + b

@srna_bp.route("/", methods=['GET'])
@crossdomain(origin='*')
def hello():
    return "Hello Language2Test!"

@srna_bp.route('/longtask', methods=['POST'])
@crossdomain(origin='*')
def longtask():
    task = add_together.delay(23, 42)
    print("\nLaunched add_together\n")
    return jsonify({ 'task_id': task.id, 'task_status': task.status }), 202, {}
#
# Celery worker needs to be started:
# celery -A app.celery worker
#