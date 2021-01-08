from srna_api.extensions import db, ma
from srna_api.providers.base_provider import BaseProvider
from srna_api.models.user_field_type import UserFieldType, UserFieldTypeSchema
from srna_api.models.enumeration import Enumeration, EnumerationSchema


class UserFieldTypeProvider(BaseProvider):

    def __get_enumeration(self, data):
        data_enumeration = data.get('enumeration')
        enumeration = None
        if data_enumeration:
            if data_enumeration.get('id') is None:
                enumeration_name = data_enumeration.get('name')
                enumeration = Enumeration.query.filter_by(name=enumeration_name).first()
            else:
                enumeration_id = data_enumeration.get('id')
                enumeration = Enumeration.query.filter_by(id=enumeration_id).first()
        return enumeration

    def add(self, data):
        data['id'] = self.generate_id(field=UserFieldType.id)
        enumeration = self.__get_enumeration(data)
        if enumeration:
            data['enumeration_id'] = enumeration.id

        user_field_type = UserFieldType(data)
        db.session.add(user_field_type)
        db.session.commit()
        return user_field_type

    def update(self, data):
        user_field_type = UserFieldType.query.filter_by(id=data.get('id')).first()
        if not user_field_type:
            user_field_type = UserFieldType.query.filter_by(name=data.get('name')).first()
        if user_field_type:
            enumeration = self.__get_enumeration(data)
            if enumeration:
                user_field_type.enumeration_id = enumeration.id
            db.session.commit()
        return user_field_type
