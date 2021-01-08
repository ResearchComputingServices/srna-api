from datetime import datetime
from srna_api.extensions import oidc
from flask import request
from srna_api.extensions import db, ma
from srna_api.providers.base_provider import BaseProvider
from srna_api.models.role import Role, RoleSchema
from srna_api.models.user import User, UserSchema
from srna_api.models.user_field import UserField, UserFieldSchema
from srna_api.models.user_field_category import UserFieldCategory, UserFieldCategorySchema
from srna_api.models.user_field_type import UserFieldType, UserFieldTypeSchema
from srna_api.models.user_field import UserField


class UserProvider(BaseProvider):
    def add(self, data):
        data['id'] = self.generate_id(field=User.id)
        user = User(data)
        for roles in data.get('roles'):
            role = Role.query.filter_by(name=roles.get('name')).first()
            if role:
                user.roles.append(role)
        db.session.add(user)
        for field in data.get('fields'):
            user_field_type = 'text'
            user_field_category = UserFieldCategory.query.filter_by(name=field.get('name')).first()
            if user_field_category:
                user_field_type = user_field_category.user_field_type.name
            field['type'] = user_field_type
            user_field = UserField(field)
            user_field.user_id = user.id
            user.fields.append(user_field)
        db.session.commit()
        return user

    def update(self, data, user):
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.agree_to_participate = data.get('agree_to_participate')
        if 'roles' in data and data.get('roles'):
            user.roles = []
            for role_item in data.get('roles'):
                role = Role.query.filter_by(name=role_item.get('name')).first()
                if role:
                    user.roles.append(role)

        for field in user.fields:
            db.session.query(UserField).filter(UserField.id == field.id).delete()

        for field in data.get('fields'):
            user_field_type = 'text'
            user_field_category = UserFieldCategory.query.filter_by(name=field.get('name')).first()
            if user_field_category:
                user_field_type = user_field_category.user_field_type.name
            field['type'] = user_field_type
            user_field = UserField(field)
            user_field.user_id= user.id
            user.fields.append(user_field)

        return user

    def delete(self, data):
        user = User.query.filter_by(id=data.get('id')).first()
        if not user:
            user = User.query.filter_by(name=data.get('name')).first()
        if user:
            for field in user.fields:
                db.session.query(UserField).filter(UserField.id == field.id).delete()
        return user

    def get_authenticated_user(self):
        auth = request.headers.get('Authorization')
        auth_fragments = auth.split(' ')
        token = auth_fragments[1]
        user_info = oidc.user_getinfo(['preferred_username', 'given_name', 'family_name'], token)
        username = user_info['preferred_username']

        # 2 Retrieve user information
        user = User.query.filter_by(name=username).first()

        return user

    def has_role(self, user, query_role):
        for role in user.roles:
            if query_role == role.name:
                return True

        return False



    def hide_roles(self, users):
        for user in users:
            user.roles = []


    def get_demographic_fields(self, user_id, start_datetime_rq, end_datetime_rq):

        demographic_fields =[]
        names = []
        user_tests =[]

        query_start_datetime = datetime.strptime(start_datetime_rq, '%Y-%m-%dT%H:%M:%S.%fZ')
        query_end_datetime = datetime.strptime(end_datetime_rq, '%Y-%m-%dT%H:%M:%S.%fZ')

        # Retrieve all student classes of the user_id
        user_student_classes = db.session.execute('SELECT * FROM student_student_class WHERE student_id = :val',
                                                  {'val': user_id})
        for item_sc in user_student_classes:
            student_class_id = item_sc['student_class_id']

        return demographic_fields


