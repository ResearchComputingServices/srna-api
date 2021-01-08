from flask import request, jsonify, url_for, Blueprint, send_file
from flask import json, jsonify, Response, blueprints
from srna_api.models.enumeration import Enumeration, EnumerationSchema
from srna_api.models.enumeration_value import EnumerationValue, EnumerationValueSchema
from srna_api.extensions import db, ma
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
from srna_api.decorators.authentication import authentication
from srna_api.providers.view_helper import ViewHelper
from srna_api.providers.enumeration_provider import EnumerationProvider
from srna_api.extensions import oidc


import pandas as pd
from srna_api.providers.raw_sql_provider import RawSqlProvider
from io import BytesIO

enumeration_schema = EnumerationSchema(many=False)
enumeration_schema_many = EnumerationSchema(many=True)

view_helper = ViewHelper()

provider = EnumerationProvider()

@srna_bp.route("/enumerations/count", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_enumeration_count():
    return view_helper.get_count(Enumeration)


@srna_bp.route("/enumerations", methods=["GET"])
@crossdomain(origin='*')
@authentication
def get_enumeration():
    id = request.args.get('id')
    if id:
        properties = Enumeration.query.filter_by(id=int(id)).first()
        result = enumeration_schema.dump(properties)
        return jsonify(result)

    name = request.args.get('name')
    if name:
        properties = Enumeration.query.filter_by(name=name).first()
        result = enumeration_schema.dump(properties)
        return jsonify(result)

    properties = view_helper.query_all(Enumeration)
    result = enumeration_schema_many.dump(properties)
    return jsonify(result)

@srna_bp.route("/enumerations", methods=['POST'])
@crossdomain(origin='*')
@authentication
def add_enumeration():
    try:
        data = request.get_json()
        enumeration = provider.add(data)
        result = enumeration_schema.dump(enumeration)
        response = jsonify(result)
    except Exception as e:
        error ={"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype = "application/json")
    return response

@srna_bp.route("/enumerations", methods=['PUT'])
@crossdomain(origin='*')
@authentication
def update_enumeration():
    try:
        data = request.get_json()
        enumeration = Enumeration.query.filter_by(id=data.get('id')).first()
        if not enumeration:
            enumeration = Enumeration.query.filter_by(name=data.get('name')).first()
        if enumeration:
            if data.get('id') is None:
                data['id'] = enumeration.id
            provider.update(data,enumeration)
            result = enumeration_schema.dump(enumeration)
            response = jsonify(result)
        else:
            response = Response(json.dumps(data), 404, mimetype = "application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype = "application/json")
    return response

@srna_bp.route("/enumerations", methods=['DELETE'])
@crossdomain(origin='*')
@authentication
def delete_enumeration():
    try:
        data = request.get_json()
        enumeration = Enumeration.query.filter_by(id=data.get('id')).first()
        if not enumeration:
            enumeration = Enumeration.query.filter_by(name=data.get('name')).first()
        if enumeration:
            if data.get('id') is None:
                data['id'] = enumeration.id
            provider.delete(data,enumeration)
            db.session.commit()
            response = Response(json.dumps(data), 200, mimetype="application/json")
        else:
            response = Response(json.dumps(data), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
    return response

@srna_bp.route("/enumerations/export", methods=['GET'])
@crossdomain(origin='*')
@authentication
def export_enumerations():
    specific_id = request.args.get('id')
    if specific_id is None:
        try:
            records = []
            enumerations = Enumeration.query.all()
            for enumeration in enumerations:
                records.append({
                    "Id": enumeration.id,
                    "Name": enumeration.name})
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame(records).to_excel(writer,
                                               sheet_name="{} summary".format("Enumeration"),
                                               index=False)
                workbook = writer.book
                worksheet = writer.sheets["{} summary".format("Enumeration")]
                format = workbook.add_format()
                format.set_align('center')
                format.set_align('vcenter')
                worksheet.set_column('A:B', 20, format)
                writer.save()
            output.seek(0)
            return send_file(output,
                             attachment_filename="Enumeration" + '.xlsx',
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             as_attachment=True, cache_timeout=-1)
        except Exception as e:
            error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
            response = Response(json.dumps(error), 404, mimetype="application/json")
            return response

    if specific_id is not None:
        try:
            name = request.args.get('name')
            if name is None:
                enum_id = request.args.get('id')
                enum = Enumeration.query.filter_by(id=enum_id).first()
                result = enumeration_schema.dump(enum)
                name = enum.name
            if name is not None:
                enum = Enumeration.query.filter_by(id=enum_id).first()
                result = enumeration_schema.dump(enum)
            enum_infos = []
            for enum_info in result['values']:
                enum_infos.append({
                    "Id":result['id'],
                    "Enumeration Name": result['name'],
                    "Enumeration Value": enum_info['text']
                })
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame(enum_infos).to_excel(writer,
                                               sheet_name="Enumeration details",
                                               index=False)
                workbook = writer.book
                worksheet = writer.sheets["Enumeration details"]
                format = workbook.add_format()
                format.set_align('center')
                format.set_align('vcenter')
                worksheet.set_column('A:C', 20, format)
                writer.save()
            output.seek(0)
            return send_file(output,
                             attachment_filename="Enumeration--{}".format(name) + '.xlsx',
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             as_attachment=True, cache_timeout=-1)
        except Exception as e:
            error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
            response = Response(json.dumps(error), 404, mimetype="application/json")
            return response

@srna_bp.route("/enumerations/upload", methods=['POST'])
@crossdomain(origin='*')
@authentication
def upload_enumerations():
    raw_data = request.get_data()
    data = pd.read_excel(raw_data, engine="openpyxl")
    try:
        enums = {}
        count = 0
        indicator = False
        for _, row in data.iterrows():
            d = dict(row)
            exist_enum = Enumeration.query.filter_by(name=d["enumeration_name"]).first()
            enum = enums.get(d["enumeration_name"])
            if enum is None and exist_enum is None:
                enum_data = {}
                enum_data["name"] = d["enumeration_name"]
                enum_data["id"] = provider.generate_id(field=Enumeration.id)
                enum = Enumeration(enum_data)
                enums[d["enumeration_name"]] = enum
                indicator = True
            if indicator:
                enum_id = provider.generate_id(field=EnumerationValue.id) + count
                count = count + 1
            else:
                enum_id = provider.generate_id(field=EnumerationValue.id)
            enum_value = EnumerationValue({"id": enum_id, "text":d["enumeration_value"]})
            if exist_enum is not None:
                if enum_value not in exist_enum.values:
                    exist_enum.values.append(enum_value)
            else:
                if enum_value not in enums[d["enumeration_name"]].values:
                    enums[d["enumeration_name"]].values.append(enum_value)
            db.session.add_all(enums.values())
            db.session.commit()
        response = Response(json.dumps({"success": True}), 200, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
    return response
