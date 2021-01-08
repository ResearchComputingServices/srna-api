from marshmallow import Schema, fields, ValidationError, pre_load
from sqlalchemy import func, ForeignKey, Sequence, Table, Column, Integer
from srna_api.extensions import db, ma
from sqlalchemy.orm import relationship
from srna_api.models.base_model import BaseModel, BaseModelSchema

class UserFieldType(BaseModel):
    __tablename__ = 'user_field_type'

    enumeration_id = db.Column(db.Integer(), ForeignKey('enumeration.id'))
    enumeration = relationship('Enumeration')

    def __init__(self, item):
        BaseModel.__init__(self, item)
        self.enumeration_id = item.get('enumeration_id')

    def __repr__(self):
        return '<user_field_type %r>' % self.name

from srna_api.models.enumeration import Enumeration, EnumerationSchema

class UserFieldTypeSchema(BaseModelSchema):
    class Meta:
        model = UserFieldType

    enumeration_id = fields.Integer()
    enumeration = fields.Nested(EnumerationSchema)
