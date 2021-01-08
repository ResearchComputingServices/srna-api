from srna_api.extensions import db, ma
from srna_api.providers.base_provider import BaseProvider
from srna_api.models.enumeration import Enumeration, EnumerationSchema
from srna_api.models.enumeration_value import EnumerationValue, EnumerationValueSchema

class EnumerationProvider(BaseProvider):
    def add(self, data):
        data['id'] = self.generate_id(field=Enumeration.id)
        enumeration = Enumeration(data)
        for index, value in enumerate(data.get('values')):
            value['id'] = self.generate_id(index, EnumerationValue.id)
            value['enumeration_id'] = data['id']
            enumeration_value = EnumerationValue(value)
            enumeration.values.append(enumeration_value)

        db.session.add(enumeration)
        db.session.commit()
        return enumeration


    def delete(self, data, enumeration):
        for value in enumeration.values:
            db.session.query(EnumerationValue).filter(EnumerationValue.id == value.id).delete()
        db.session.query(Enumeration).filter(Enumeration.id == data.get('id')).delete()


    def update(self, data, enumeration):
        for value in enumeration.values:
            db.session.query(EnumerationValue).filter(EnumerationValue.id == value.id).delete()

        for index, value in enumerate(data.get('values')):
            value['id'] = self.generate_id(index, EnumerationValue.id)
            value['enumeration_id'] = data['id']
            enumeration_value = EnumerationValue(value)
            enumeration.values.append(enumeration_value)
        db.session.commit()
        return enumeration
