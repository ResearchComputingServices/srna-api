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
    time.sleep(10)
    print("\nadd_together processing\n")
    return a + b

@srna_bp.route("/", methods=['GET'])
@crossdomain(origin='*')
@authentication
def hello():
    return "Hello Language2Test!"

@srna_bp.route('/longtask', methods=['POST'])
@crossdomain(origin='*')
@authentication
def longtask():
    task = add_together.delay(23, 42)
    print("\nLaunched long_task processing\n")
    return jsonify({ 'task_id': task.id, 'task_status': task.status }), 202, {}
#
# Celery worker needs to be started:
# celery -A app.celery worker
#