from srna_api.extensions import db, ma
from srna_api.providers.base_provider import BaseProvider
from srna_api.models.role import Role, RoleSchema
from srna_api.models.authorization import Authorization, AuthorizationSchema

class RoleProvider(BaseProvider):
    def add(self, data):
        data['id'] = self.generate_id(field=Role.id)
        role = Role(data)
        for authorization_item in data.get('authorizations'):
            if 'id' in authorization_item:
                authorization = Authorization.query.filter_by(id=authorization_item.get('id')).first()
            else:
                authorization = Authorization.query.filter_by(name=authorization_item.get('name')).first()
            if authorization:
                role.authorizations.append(authorization)
        db.session.add(role)
        db.session.commit()
        return role


    def update(self, data, role):
        role.authorizations = []
        for authorization_item in data.get('authorizations'):
            if 'id' in authorization_item:
                authorization = Authorization.query.filter_by(id=authorization_item.get('id')).first()
            else:
                authorization = Authorization.query.filter_by(name=authorization_item.get('name')).first()
            if authorization:
                role.authorizations.append(authorization)
        return role