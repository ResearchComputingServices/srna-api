from srna_api.extensions import db, ma
from srna_api.providers.base_provider import BaseProvider
from srna_api.models.user_field_category import UserFieldCategory, UserFieldCategorySchema
from srna_api.models.user_field_type import UserFieldType, UserFieldTypeSchema

class UserFieldCategoryProvider(BaseProvider):
    def add(self, data):
        data['id'] = self.generate_id(field=UserFieldCategory.id)
        data = self.fill_out_name_based_on_display(data)
        data_user_field_type = data.get('user_field_type')
        if data_user_field_type:
            user_field_type_name = data_user_field_type.get('name')
            user_field_type = UserFieldType.query.filter_by(name=user_field_type_name).first()
            if user_field_type:
                data['user_field_type_id'] = user_field_type.id
        user_field_category = UserFieldCategory(data)
        db.session.add(user_field_category)
        return user_field_category

    def delete(self, data, user_field_category):
        return

    def update(self, data, user_field_category):
        data_user_field_type = data.get('user_field_type')
        if data_user_field_type:
            user_field_type_name = data_user_field_type.get('name')
            user_field_type = UserFieldType.query.filter_by(name=user_field_type_name).first()
            if user_field_type:
                data['user_field_type_id'] = user_field_type.id
        user_field_category.display = data.get('display')
        user_field_category.user_field_type_id = data.get('user_field_type_id')
        return user_field_category
