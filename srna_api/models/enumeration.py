from marshmallow import Schema, fields, ValidationError, pre_load
from sqlalchemy.orm import relationship
from srna_api.models.base_model import BaseModel, BaseModelSchema

class Enumeration(BaseModel):
    __tablename__= 'enumeration'

    values = relationship ("EnumerationValue", back_populates = "enumeration")

    def __init__(self, item):
        BaseModel.__init__(self, item)

    def __repr__(self):
        return '<enumeration %r>' %self.id

from srna_api.models.enumeration_value import EnumerationValue, EnumerationValueSchema

class EnumerationSchema(BaseModelSchema):
    class Meta:
        model = Enumeration

    values = fields.Nested(EnumerationValueSchema, many=True)

