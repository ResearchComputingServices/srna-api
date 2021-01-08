from flask import request, send_file
from flask import json, jsonify, Response
from srna_api.models.role import Role, RoleSchema
from srna_api.models.user import User, UserSchema
from srna_api.models.user_field import UserField
from srna_api.extensions import db, ma
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
from srna_api.decorators.authentication import authentication
from srna_api.decorators.authorization import authorization
from srna_api.providers.user_provider import UserProvider
from srna_api.models.user_field import UserFieldSchema
from srna_api.models.user_field_category import UserFieldCategorySchema
from srna_api.web.user_keycloak import UserKeycloak
from srna_api.extensions import oidc
import pandas as pd
import math
from io import BytesIO

user_schema = UserSchema(many=False)
user_schema_many = UserSchema(many=True)
user_field_schema_many = UserFieldSchema(many=True)
user_field_category_schema_many = UserFieldCategorySchema(many=True)

provider = UserProvider()
keycloak = UserKeycloak()


@srna_bp.route('/users/login', methods=['GET'])
@crossdomain(origin='*')
@authentication
def login():
    error = { 'error': 'Permission Denied' }
    auth = request.headers.get('Authorization')
    if not auth:
        return Response(json.dumps(error), 403, mimetype='application/json')
    auth_fragments = auth.split(' ')
    if len(auth_fragments) < 2 or auth_fragments[0] != 'Bearer':
        return Response(json.dumps(error), 403, mimetype='application/json')
    token = auth_fragments[1]
    try:
        user_info = oidc.user_getinfo(['preferred_username', 'given_name', 'family_name'], token)
        name = user_info['preferred_username']
        first_name = user_info['given_name']
        last_name = user_info['family_name']
        user = User.query.filter_by(name=name).first()
        if not user:
            user = provider.add({
                'name': name,
                'first_name': first_name,
                'last_name': last_name,
                'roles': [{ 'name': 'Test Taker'}],
                'fields': []
            })
            return jsonify(user_schema.dump(user))
        return jsonify(user_schema.dump(user))
    except Exception as e:
        return Response(json.dumps(error), 403, mimetype='application/json')
    return Response(error, 403, mimetype='application/json')

@srna_bp.route("/users/count", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_user_count():
    roles_param = request.args.get('roles')
    users = User.query
    if roles_param:
        roles_param = tuple(roles_param.split(','))
        roles = Role.query.filter(Role.name.in_(roles_param)).all()
        users = users.join(User.roles).filter(Role.id.in_(role.id for role in roles))
    count = users.count()
    dict = {"count": count}
    response = Response(json.dumps(dict), 200, mimetype="application/json")
    return response


@srna_bp.route("/users", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_user():
    try:
        id = request.args.get('id')
        name = request.args.get('name')
        roles_param = request.args.get('roles')
        users = User.query
        if roles_param:
            roles_param = tuple(roles_param.split(','))
            roles = Role.query.filter(Role.name.in_(roles_param)).all()
            users = users.join(User.roles).filter(Role.id.in_(role.id for role in roles))
        if id:
            properties = users.filter_by(id=id).first()
        elif name:
            properties = users.filter_by(name=name).first()
        else:
            properties = provider.query_all_by_subquery(users, 'user')
        result = user_schema.dump(properties) if (type(properties) is User) else user_schema_many.dump(properties)
        response = jsonify(result)
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

@srna_bp.route("/users", methods=['POST'])
@crossdomain(origin='*')
@authentication
def add_user():
    try:
        data = request.get_json()
        user = provider.add(data)
        if user:
            user_dict = {}
            user_dict['User Name'] = user.name
            user_dict['First Name'] = user.first_name
            user_dict['Last Name'] = user.last_name
            __import_user_in_keycloak(user_dict, [])
            if (user_dict['kc_status_code']<200) or (user_dict['kc_status_code']>300):
                #User couldn't be imported into keycloak
                #Adding is transactional
                #We'll revert the adding of user into a db.
                user = provider.delete(data)
                db.session.delete(user)
                db.session.commit()
                error = {"message": "User cannot be created on Keycloak"}
                response = Response(json.dumps(error), user_dict['kc_status_code'], mimetype="application/json")
            else:
                result = user_schema.dump(user)
                response = jsonify(result)
        else:
            response = Response(json.dumps(data), 500, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

@srna_bp.route("/users/reset_keycloak_password", methods=['PUT'])
@crossdomain(origin='*')
@authentication
def reset_user_keycloak_password():
    try:
        user_auth = provider.get_authenticated_user()
        if user_auth:
            is_admin = provider.has_role(user_auth, 'Administrator')
            if is_admin:
                data = request.get_json()
                user = User.query.filter_by(id=data.get('id')).first()
                if not user:
                    user = User.query.filter_by(name=data.get('name')).first()
                if user:
                    status_code = keycloak.reset_user_password(user, data)
                    if status_code>=200 and status_code<=300:
                        result = user_schema.dump(user)
                        response = jsonify(result)
                    else:
                        response = Response(json.dumps(data), status_code, mimetype="application/json")
                else:
                    response = Response(json.dumps(data), 404, mimetype="application/json")
            else:
                error = {"message": "Permission Denied"}
                response = Response(json.dumps(error), 403, mimetype="application/json")
        else:
            error = {"message": "User not found."}
            response = Response(json.dumps(error), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
    return response



@srna_bp.route("/users/demographic_questionnaire", methods=['PUT'])
@crossdomain(origin='*')
@authentication
def update_demographic_questionnaire():
 try:
    data = request.get_json()
    auth = request.headers.get('Authorization')
    auth_fragments = auth.split(' ')
    token = auth_fragments[1]
    name = oidc.user_getfield('preferred_username', token)
    user = User.query.filter_by(name=name).first()
    if user:
        if data.get('id') is None:
            data['id'] = user.id
        provider.update(data, user)
        db.session.commit()
        response = Response(json.dumps(data), 200, mimetype="application/json")
    else:
        response = Response(json.dumps(data), 404, mimetype="application/json")
 except Exception as e:
    error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
    response = Response(json.dumps(error), 500, mimetype="application/json")
 return response



@srna_bp.route("/users", methods=['PUT'])
@crossdomain(origin='*')
@authentication
def update_user():
    try:
        data = request.get_json()
        user = User.query.filter_by(id=data.get('id')).first()
        if not user:
            user = User.query.filter_by(name=data.get('name')).first()
        if user:
            if data.get('id') is None:
                data['id'] = user.id
            provider.update(data, user)
            db.session.commit()
            response = Response(json.dumps(data), 200, mimetype="application/json")
        else:
            response = Response(json.dumps(data), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

@srna_bp.route("/users", methods=['DELETE'])
@crossdomain(origin='*')
@authentication
def delete_user():
    try:
        data = request.get_json()
        user = User.query.filter_by(id=data.get('id')).first()
        if not user:
            user = User.query.filter_by(name=data.get('name')).first()
        if user:
            user = provider.delete(data)
            db.session.delete(user)
            db.session.commit()
            response = Response(json.dumps(data), 200, mimetype="application/json")
        else:
            response = Response(json.dumps(data), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response

@srna_bp.route("/users/export", methods=['GET'])
@crossdomain(origin='*')
@authentication
def export_users():
    specific_id = request.args.get('id')
    if specific_id is None:
        try:
            records = []
            users = User.query.all()
            for i in range(len(users)):
                s_u = User.query.filter_by(id=(i+1)).first()
                result = user_schema.dump(s_u)
                u_f = result['fields']
                if u_f == []:
                    student_id = ''
                    first_language = ''
                    email = ''
                    phone = ''
                    address = ''
                    education = ''
                else:
                    for info in u_f:
                        if info['name'] == 'student_id':
                            student_id = info['value']
                            break
                        else:
                            student_id = ''
                    for info in u_f:
                        if info['name'] == 'first_language':
                            first_language = info['value']
                            break
                        else:
                            first_language = ''
                    for info in u_f:
                        if info['name'] == 'email':
                            email = info['value']
                            break
                        else:
                            email = ''
                    for info in u_f:
                        if info['name'] == 'phone':
                            phone = info['value']
                            break
                        else:
                            phone = ''
                    for info in u_f:
                        if info['name'] == 'address':
                            address = info['value']
                            break
                        else:
                            address = ''
                    for info in u_f:
                        if info['name'] == 'education':
                            education = info['value']
                            break
                        else:
                            education = ''
                records.append({
                    "Id": s_u.id,
                    "User Name": s_u.name,
                    "First Name": s_u.first_name,
                    "Last Name": s_u.last_name,
                    "Roles": ", ".join(map(lambda e: e.name, s_u.roles)),
                    "Student ID": student_id,
                    "First Language": first_language,
                    "Email": email,
                    "Phone": phone,
                    "Address": address,
                    "Education": education
                })

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame(records).to_excel(writer,
                                               sheet_name="{} summary".format("User"),
                                               index=False)
                workbook = writer.book
                worksheet = writer.sheets["{} summary".format("User")]
                format = workbook.add_format()
                format.set_align('center')
                format.set_align('vcenter')
                worksheet.set_column('A:D', 18, format)
                worksheet.set_column('E:E', 28, format)
                worksheet.set_column('F:G', 22, format)
                worksheet.set_column('H:H', 28, format)
                worksheet.set_column('I:K', 18, format)
                writer.save()
            output.seek(0)
            return send_file(output,
                             attachment_filename= "User list" + '.xlsx',
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
                user_id = request.args.get('id')
                s_u = User.query.filter_by(id=user_id).first()
                result = user_schema.dump(s_u)
                u_f = result['fields']
                name = s_u.name
            else:
                s_u = User.query.filter_by(name=name).first()
            if u_f == []:
                student_id = ''
                first_language = ''
                email = ''
                phone = ''
                address = ''
                education = ''
            else:
                for info in u_f:
                    if info['name'] == 'student_id':
                        student_id = info['value']
                        break
                    else:
                        student_id = ''
                for info in u_f:
                    if info['name'] == 'first_language':
                        first_language = info['value']
                        break
                    else:
                        first_language = ''
                for info in u_f:
                    if info['name'] == 'email':
                        email = info['value']
                        break
                    else:
                        email = ''
                for info in u_f:
                    if info['name'] == 'phone':
                        phone = info['value']
                        break
                    else:
                        phone = ''
                for info in u_f:
                    if info['name'] == 'address':
                        address = info['value']
                        break
                    else:
                        address = ''
                for info in u_f:
                    if info['name'] == 'education':
                        education = info['value']
                        break
                    else:
                        education = ''

            specific_user_info = [{
                "Id": s_u.id,
                "User Name": s_u.name,
                "First Name": s_u.first_name,
                "Last Name": s_u.last_name,
                "Roles": ", ".join(map(lambda e: e.name, s_u.roles)),
                "Student ID": student_id,
                "First Language": first_language,
                "Email": email,
                "Phone": phone,
                "Address": address,
                "Education": education
                }]

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame(specific_user_info).to_excel(writer,
                                               sheet_name="User {} summary".format(name),
                                               index=False)
                workbook = writer.book
                worksheet = writer.sheets["User {} summary".format(name)]
                format = workbook.add_format()
                format.set_align('center')
                format.set_align('vcenter')
                worksheet.set_column('A:D', 18, format)
                worksheet.set_column('E:E', 28, format)
                worksheet.set_column('F:G', 22, format)
                worksheet.set_column('H:H', 28, format)
                worksheet.set_column('I:K', 18, format)
                writer.save()

            output.seek(0)
            return send_file(output,
                             attachment_filename= "User "+ name + '.xlsx',
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             as_attachment=True, cache_timeout=-1)
        except Exception as e:
            response = Response(json.dumps(e), 404, mimetype="application/json")
            return response

def __import_report(users):
    try:
        records = []
        for user in users:
            if type(user["User Name"]) == str:
                records.append({
                    "User Name": user['User Name'],
                    "First Name": user['First Name'],
                    "Last Name": user['Last Name'],
                    "Password": user['Password'],
                    "DB Import result": user['db_import'],
                    "Keycloak Import result": user['kc_import']})

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame(records).to_excel(writer,
                                               sheet_name="{} summary".format("User"),
                                               index=False)
            workbook = writer.book
            worksheet = writer.sheets["{} summary".format("User")]
            format = workbook.add_format()
            format.set_align('center')
            format.set_align('vcenter')
            worksheet.set_column('A:D', 18, format)
            worksheet.set_column('E:E', 28, format)
            writer.save()
        output.seek(0)
        return send_file(output,attachment_filename= "Import Result" + '.xlsx',mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",as_attachment=True, cache_timeout=-1)
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred when writing Excel report of Import Users action."}
        response = Response(json.dumps(error), 404, mimetype="application/json")
        return response


def __import_user_in_db(d):
    try:
        user = []
        if type(d["User Name"]) == str:
            user = User.query.filter_by(name=d["User Name"]).first()
            if user is not None:
                marked = {}

                for field in user.fields:
                    if field.name == "student_id":
                        marked["student_id"] = True
                        field.value = str(d["Student ID"]).replace(".0", "") if not math.isnan(d["Student ID"]) else None
                    elif field.name == "first_language":
                        marked["first_language"] = True
                        field.value = d["First Language"] if type(d["First Language"]) != float else None
                    elif field.name == "email":
                        marked["email"] = True
                        field.value = d["Email"] if type(d["Email"]) != float else None
                    elif field.name == "education":
                        marked["education"] = True
                        field.value = d["Education"] if type(d["Education"]) != float else None
                    elif field.name == "phone":
                        marked["phone"] = True
                        field.value = str(d["Phone"]).replace(".0", "") if not math.isnan(d["Phone"]) else None
                    elif field.name == "address":
                        marked["address"] = True
                        field.value = d["Address"] if type(d["Address"]) != float else None
                if not marked.get("student_id", False):
                    user.fields.append(UserField(
                        {"name": "student_id", "type": "text", "value": str(d["Student ID"]).replace(".0", "") if not math.isnan(d["Student ID"]) else None, "user_id": user.id}))
                if not marked.get("first_language", False):
                    user.fields.append(UserField(
                        {"name": "first_language", "type": "Language",
                         "value": d["First Language"] if type(d["First Language"]) != float else None, "user_id": user.id}))
                if not marked.get("email", False):
                    user.fields.append(UserField(
                        {"name": "email", "type": "text", "value": d["Email"] if type(d["Email"]) != float else None, "user_id": user.id}))
                if not marked.get("education", False):
                    user.fields.append(UserField(
                        {"name": "education", "type": "University", "value": d["Education"] if type(d["Education"]) != float else None, "user_id": user.id}))
                if not marked.get("phone", False):
                    user.fields.append(UserField(
                        {"name": "phone", "type": "text", "value": str(d["Phone"]).replace(".0", "") if not math.isnan(d["Phone"]) else None, "user_id": user.id}))
                if not marked.get("address", False):
                    user.fields.append(UserField(
                        {"name": "address", "type": "text", "value": d["Address"] if type(d["Address"]) != float else None, "user_id": user.id}))
                d['db_import'] = 'Updated'
            else:
                user_data = {}
                user_data["name"] = d["User Name"]
                user_data["first_name"] = d["First Name"]
                user_data["last_name"] = d["Last Name"]
                user_data["id"] = provider.generate_id(field=User.id)
                user = User(user_data)
                role = Role.query.filter_by(name="Test Taker").first()
                user.roles.append(role)
                user.fields.append(UserField(
                    {"name": "student_id", "type": "text", "value": str(d["Student ID"]).replace(".0", "") if not math.isnan(d["Student ID"]) else None, "user_id": user.id}))
                user.fields.append(UserField(
                    {"name": "first_language", "type": "Language",
                     "value": d["First Language"] if type(d["First Language"]) != float else None, "user_id": user.id}))
                user.fields.append(UserField(
                    {"name": "email", "type": "text", "value": d["Email"] if type(d["Email"]) != float else None, "user_id": user.id}))
                user.fields.append(UserField(
                    {"name": "education", "type": "University", "value": d["Education"] if type(d["Education"]) != float else None, "user_id": user.id}))
                user.fields.append(UserField(
                    {"name": "phone", "type": "text", "value": str(d["Phone"]).replace(".0", "") if not math.isnan(d["Phone"]) else None, "user_id": user.id}))
                user.fields.append(UserField(
                    {"name": "address", "type": "text", "value": d["Address"] if type(d["Address"]) != float else None, "user_id": user.id}))
                d['db_import'] = 'Imported'
            db.session.add(user)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        user = []
        d['db_import'] = 'Error: ' + str(e)
    return user


def  __import_user_in_keycloak(user_dict, token):
    # Password for keycloak import
    if ('Password' in user_dict):
        user_password = user_dict['Password']
        # Check for empty password
        # If empty password assign username as password
        if type(user_password) != str and math.isnan(user_password):
            user_password = user_dict["User Name"]
    else:
        user_password = user_dict["User Name"]
    user_dict['Password'] = user_password

    # Import user into keycloak
    token = keycloak.import_user(user_dict, token)
    return token


@srna_bp.route("users/upload", methods=['POST'])
@crossdomain(origin='*')
@authentication
def import_users():
    raw_data = request.get_data()
    data = pd.read_excel(raw_data, engine="openpyxl")
    list_users = []
    token_kc = []
    try:
        for _, row in data.iterrows():
            d = dict(row)
            user = __import_user_in_db(d)

            #User was sucessfully imported or updated in DB
            if user :
                token_kc = __import_user_in_keycloak(d, token_kc)
            else:
                d['kc_import'] = 'Import Cancelled'

            list_users.append(d)


        response = __import_report(list_users)

    except Exception as e:

        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response


@srna_bp.route("/test_taker/demographic_questionnaires", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_demographic_questionnaire():
    try:
        start_datetime_rq = request.args.get('start_datetime')
        end_datetime_rq = request.args.get('end_datetime')

        user = provider.get_authenticated_user()
        if user:
            is_test_taker = provider.has_role(user, 'Test Taker')
            if is_test_taker:
                test_taker_id =user.id
                properties = provider.get_demographic_fields(test_taker_id, start_datetime_rq, end_datetime_rq)
                #result = user_field_schema_many.dump(properties)
                result = user_field_category_schema_many.dump(properties)
                return jsonify(result)
            else:
                error = {"message": "Permission Denied"}
                response = Response(json.dumps(error), 403, mimetype="application/json")
        else:
            error = {"message": "User not found."}
            response = Response(json.dumps(error), 404, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")

    return response



@srna_bp.route("/admin/user_sessions", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_user_sessions():
    try:
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        user = provider.get_authenticated_user()
        is_admin = provider.has_role(user, 'Administrator')
        if is_admin:
            response = jsonify(keycloak.get_user_sessions(oidc.client_secrets['realm'],offset,limit))
        else:
            error = {"message": "Access Denied"}
            response = Response(json.dumps(error), 403, mimetype="application/json")


    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
    return response


@srna_bp.route("/admin/user_sessions/count", methods=['GET'])
@crossdomain(origin='*')
@authentication
def get_user_sessions_count():
    try:
        user = provider.get_authenticated_user()
        is_admin = provider.has_role(user, 'Administrator')
        if is_admin:
            response = keycloak.get_user_sessions_count(oidc.client_secrets['realm'])
        else:
            error = {"message": "Access Denied"}
            response = Response(json.dumps(error), 403, mimetype="application/json")
    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
    return response

