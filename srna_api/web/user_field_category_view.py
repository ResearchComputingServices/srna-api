from flask import request, send_file
from flask import json, jsonify, Response
from srna_api.models.user_field_category import UserFieldCategory, UserFieldCategorySchema
from srna_api.models.user_field_type import UserFieldType, UserFieldTypeSchema
from srna_api.extensions import db, ma
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
from srna_api.decorators.authentication import authentication
from srna_api.providers.user_field_category_provider import UserFieldCategoryProvider

import pandas as pd
from io import BytesIO

user_field_category_schema = UserFieldCategorySchema(many=False)
user_field_category_schema_many = UserFieldCategorySchema(many=True)

provider = UserFieldCategoryProvider()

@srna_bp.route("/user_field_categories/count", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_user_field_categories_count():
    return provider.get_count(UserFieldCategory)

@srna_bp.route("/user_field_categories", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_user_field_category():
    id = request.args.get('id')
    if id:
        properties = UserFieldCategory.query.filter_by(id=int(id)).first()
        result = user_field_category_schema.dump(properties)
        return jsonify(result)

    name = request.args.get('name')
    type = request.args.get('type')
    display = request.args.get('display')
    if name and not type:
        properties = UserFieldCategory.query.filter_by(name=name)
        result = user_field_category_schema.dump(properties)
        return jsonify(result)

    if name and type:
        type_properties = UserFieldType.query.filter_by(name=type).first()
        user_field_type_id = type_properties.id
        properties = UserFieldCategory.query.filter(UserFieldCategory.name == name).filter(UserFieldCategory.user_field_type_id == user_field_type_id).first()
        result = user_field_category_schema.dump(properties)
        return jsonify(result)

    if not name and type:
        type_properties = UserFieldType.query.filter_by(name=type).first()
        user_field_type_id = type_properties.id
        properties = UserFieldCategory.query.filter(UserFieldCategory.user_field_type_id == user_field_type_id)
        result = user_field_category_schema_many.dump(properties)
        return jsonify(result)

    if display:
        properties = UserFieldCategory.query.filter(UserFieldCategory.display == display).first()
        result = user_field_category_schema.dump(properties)
        return jsonify(result)

    properties = provider.query_all(UserFieldCategory)
    result = user_field_category_schema_many.dump(properties)
    return jsonify(result)

@srna_bp.route("/user_field_categories", methods=['POST'])
@crossdomain(origin='*')
@authentication
def add_user_field_category():
    try:
        data = request.get_json()
        user_field_category = provider.add(data)
        db.session.commit()
        result = user_field_category_schema.dump(user_field_category)
        response = jsonify(result)
    except Exception as e:
        error = { "exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

@srna_bp.route("/user_field_categories", methods=['PUT'])
@crossdomain(origin='*')
@authentication
def update_user_field_category():
    data = request.get_json()
    user_field_category = UserFieldCategory.query.filter_by(id=data.get('id')).first()
    if not user_field_category:
        user_field_category = UserFieldCategory.query.filter_by(name=data.get('name')).first()
    if user_field_category:
        provider.update(data, user_field_category)
        db.session.commit()
        response = Response(json.dumps(data), 200, mimetype="application/json")
    else:
        response = Response(json.dumps(data), 404, mimetype="application/json")

    return response

@srna_bp.route("/user_field_categories", methods=['DELETE'])
@crossdomain(origin='*')
@authentication
def delete_user_field_category():
    data = request.get_json()
    user_field_category = UserFieldCategory.query.filter_by(id=data.get('id')).first()
    if not user_field_category:
        user_field_category = UserFieldCategory.query.filter_by(name=data.get('name')).first()
    if user_field_category:
        db.session.delete(user_field_category)
        db.session.commit()
        response = Response(json.dumps(data), 200, mimetype="application/json")
    else:
        response = Response(json.dumps(data), 404, mimetype="application/json")

    return response

@srna_bp.route("/user_field_categories/export", methods=['GET'])
@crossdomain(origin='*')
@authentication
def export_demographic_field():
    specific_id = request.args.get('id')
    if specific_id is None:
        try:
            records = []
            fields = UserFieldCategory.query.all()
            for f in fields:
                records.append({
                    "Id": f.id,
                    "Name": f.display,
                    "Type": f.user_field_type.name})

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame(records).to_excel(writer,
                                               sheet_name="{} summary".format("Demographic Fields"),
                                               index=False)
                workbook = writer.book
                worksheet = writer.sheets["{} summary".format("Demographic Fields")]
                format = workbook.add_format()
                format.set_align('center')
                format.set_align('vcenter')
                worksheet.set_column('A:C', 20, format)
                writer.save()

            output.seek(0)
            return send_file(output,
                             attachment_filename="Demographic Fields" + '.xlsx',
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
                ufc_id = request.args.get('id')
                ufc = UserFieldCategory.query.filter_by(id=ufc_id).first()
                result = user_field_category_schema.dump(ufc)
                name = ufc.name
            if name is not None:
                ufc = UserFieldCategory.query.filter_by(id=ufc_id).first()
                result = user_field_category_schema.dump(ufc)
            ufc_infos = {
                "Id": result['id'],
                "Name": result['display'],
                "Type": result['user_field_type']['name']
            }

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame([ufc_infos]).to_excel(writer,
                                               sheet_name="{} details".format("Demographic Fields"),
                                               index=False)
                workbook = writer.book
                worksheet = writer.sheets["{} details".format("Demographic Fields")]
                format = workbook.add_format()
                format.set_align('center')
                format.set_align('vcenter')
                worksheet.set_column('A:C', 15, format)
                writer.save()
            output.seek(0)
            return send_file(output,
                             attachment_filename="Demographic Fields" + '.xlsx',
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             as_attachment=True, cache_timeout=-1)
        except Exception as e:
            error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
            response = Response(json.dumps(error), 404, mimetype="application/json")
            return response
