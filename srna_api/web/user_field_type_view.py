from flask import request, send_file
from flask import json, jsonify, Response
from srna_api.models.user_field_type import UserFieldType, UserFieldTypeSchema
from srna_api.extensions import db, ma
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
from srna_api.decorators.authentication import authentication
from srna_api.providers.user_field_type_provider import UserFieldTypeProvider
import pandas as pd
from io import BytesIO
user_field_type_schema = UserFieldTypeSchema(many=False)
user_field_type_schema_many = UserFieldTypeSchema(many=True)

provider = UserFieldTypeProvider()

@srna_bp.route("/user_field_types/count", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_user_field_types_count():
    return provider.get_count(UserFieldType)

@srna_bp.route("/user_field_types", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_user_field_type():
    id = request.args.get('id')
    if id:
        properties = UserFieldType.query.filter_by(id=id).first()
        result = user_field_type_schema.dump(properties)
        return jsonify(result)

    name = request.args.get('name')
    if name:
        properties = UserFieldType.query.filter_by(name=name).first()
        result = user_field_type_schema.dump(properties)
        return jsonify(result)

    properties = provider.query_all(UserFieldType)
    result = user_field_type_schema_many.dump(properties)
    return jsonify(result)


@srna_bp.route("/user_field_types", methods=['POST'])
@crossdomain(origin='*')
@authentication
def add_user_field_type():
    try:
        data = request.get_json()
        user_field_type = provider.add(data)
        result = user_field_type_schema.dump(user_field_type)
        response = jsonify(result)
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

@srna_bp.route("/user_field_types", methods=['PUT'])
@crossdomain(origin='*')
@authentication
def update_user_field_type():
    try:
        data = request.get_json()
        user_field_type = provider.update(data)
        if user_field_type:
            db.session.commit()
            response = Response(json.dumps(data), 200, mimetype="application/json")
        else:
            response = Response(json.dumps(data), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

@srna_bp.route("/user_field_types", methods=['DELETE'])
@crossdomain(origin='*')
@authentication
def delete_user_field_type():
    try:
        data = request.get_json()
        user_field_type = UserFieldType.query.filter_by(id=data.get('id')).first()
        if not user_field_type:
            user_field_type = UserFieldType.query.filter_by(name=data.get('name')).first()
        if user_field_type:
            db.session.delete(user_field_type)
            db.session.commit()
            response = Response(json.dumps(data), 200, mimetype="application/json")
        else:
            response = Response(json.dumps(data), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
    return response

@srna_bp.route("/user_field_types/export", methods=['GET'])
@crossdomain(origin='*')
@authentication
def export_user_field_types():
    specific_id = request.args.get('id')
    if specific_id is None:
        try:
            records = []
            fields = UserFieldType.query.all()
            for f in fields:
                records.append({
                    "Id": f.id,
                    "Name": f.name,
                    "Enumeration": f.enumeration.name if f.enumeration is not None else None})
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame(records).to_excel(writer,
                                               sheet_name="{} summary".format("user field type"),
                                               index=False)
                workbook = writer.book
                worksheet = writer.sheets["{} summary".format("user field type")]
                format = workbook.add_format()
                format.set_align('center')
                format.set_align('vcenter')
                worksheet.set_column('A:C', 20, format)
                writer.save()

            output.seek(0)
            return send_file(output,
                             attachment_filename="User Field Type Summary" + '.xlsx',
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             as_attachment=True, cache_timeout=-1)
        except Exception as e:
            error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
            response = Response(json.dumps(error), 404, mimetype="application/json")
            return response

    if specific_id is not None:
        try:
            fields = UserFieldType.query.all()
            for field in fields:
                if field.id == int(specific_id):
                    specific_type = field
                    break
            records = {
                "Id": specific_type.id,
                "Name": specific_type.name,
                "Enumeration": specific_type.enumeration.name if specific_type.enumeration is not None else None
            }

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame([records]).to_excel(writer,
                                               sheet_name="{} details".format("user field type"),
                                               index=False)
                workbook = writer.book
                worksheet = writer.sheets["{} details".format("user field type")]
                format = workbook.add_format()
                format.set_align('center')
                format.set_align('vcenter')
                worksheet.set_column('A:C', 15, format)
                writer.save()
            output.seek(0)
            return send_file(output,
                             attachment_filename="User Field Type Details" + '.xlsx',
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             as_attachment=True, cache_timeout=-1)
        except Exception as e:
            error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
            response = Response(json.dumps(error), 404, mimetype="application/json")
            return response

