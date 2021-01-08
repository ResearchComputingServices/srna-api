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

@srna_bp.route("/", methods=['GET'])
@crossdomain(origin='*')
@authentication
def hello():
    return "Hello Language2Test!"

