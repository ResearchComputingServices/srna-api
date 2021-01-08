from flask import request
from flask import json, jsonify, Response, blueprints
from srna_api.models.authorization import Authorization, AuthorizationSchema
from srna_api.extensions import db, ma
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
from srna_api.decorators.authentication import authentication
from srna_api.decorators.authorization import authorization
from srna_api.providers.base_provider import BaseProvider

authorization_schema = AuthorizationSchema(many=False)
authorization_schema_many = AuthorizationSchema(many=True)

provider = BaseProvider()

@srna_bp.route("/authorization/count", methods=['GET'])
@crossdomain(origin='*')
@authentication
@authorization(['read-authorization'])
def get_authorization_count():
    return provider.get_count(Authorization)


@srna_bp.route("/authorization", methods=['GET'])
@crossdomain(origin='*')
@authentication
@authorization(['read-authorization'])
def get_authorization():
    id = request.args.get('id')
    if id:
        properties = Authorization.query.filter_by(id=id).first()
        result = authorization_schema.dump(properties)
        return jsonify(result)

    name = request.args.get('name')
    if name:
        properties = Authorization.query.filter_by(name=name).first()
        result = authorization_schema.dump(properties)
        return jsonify(result)

    properties = provider.query_all(Authorization)
    result = authorization_schema_many.dump(properties)
    return jsonify(result)


def add_authorization():
    try:
        data = request.get_json()
        authorization = Authorization(data)
        db.session.add(authorization)
        db.session.commit()
        result = authorization_schema.dump(authorization)
        response = jsonify(result)
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

def update_authorization():
    try:
        data = request.get_json()
        authorization = Authorization.query.filter_by(id=data.get('id')).first()
        if not authorization:
            authorization = Authorization.query.filter_by(name=data.get('name')).first()
        if authorization:
            if 'text' in data:
                authorization.text = data.get('text')
            db.session.commit()
            response = Response(json.dumps(data), 200, mimetype="application/json")
        else:
            response = Response(json.dumps(data), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

def delete_authorization():
    try:
        data = request.get_json()
        authorization = Authorization.query.filter_by(id=data.get('id')).first()
        if not authorization:
            authorization = Authorization.query.filter_by(name=data.get('name')).first()
        if authorization:
            db.session.delete(authorization)
            db.session.commit()
            response = Response(json.dumps(data), 200, mimetype="application/json")
        else:
            response = Response(json.dumps(data), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
    return response