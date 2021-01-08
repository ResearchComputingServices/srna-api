from marshmallow import Schema, fields, ValidationError, pre_load
from sqlalchemy import func, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from srna_api.extensions import db, ma
from srna_api.models.base_model import BaseModel, BaseModelSchema
from srna_api.models.user_field_type import UserFieldType, UserFieldTypeSchema
from srna_api.models.base_model import BaseModel, BaseModelSchema

class UserFieldCategory(BaseModel):
    __tablename__ = 'user_field_category'

    display = db.Column(db.String())
    user_field_type_id = db.Column(db.Integer(), ForeignKey('user_field_type.id'))
    user_field_type = relationship("UserFieldType")

    def __init__(self, item):
        BaseModel.__init__(self, item)
        self.display = item.get('display')
        self.user_field_type_id = item.get('user_field_type_id')

    def __repr__(self):
        return '<user_field_category %s, %s>' % (self.user_id, str(self.created_datetime))

class UserFieldCategorySchema(BaseModelSchema):
    class Meta:
        model = UserFieldCategory

    display = fields.String()
    user_field_type = fields.Nested(UserFieldTypeSchema)
    user_field_type_id = fields.Integer()

