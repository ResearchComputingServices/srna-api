from marshmallow import Schema, fields, ValidationError, pre_load
from sqlalchemy import func, ForeignKey, Sequence, Table, Column, Integer
from sqlalchemy.orm import relationship
from srna_api.extensions import db, ma
from srna_api.models.base_text_model import BaseTextModel, BaseTextModelSchema

class EnumerationValue(BaseTextModel):
    __tablename__='enumeration_value'

    enumeration_id = db.Column(db.Integer(), ForeignKey('enumeration.id'))
    enumeration = relationship('Enumeration', back_populates = 'values')

    def __init__(self, item):
        BaseTextModel.__init__(self, item)
        self.enumeration_id = item.get('enumeration_id')


    def __repr__(self):
        return '<enumeration_value %r>' % self.id


class EnumerationValueSchema(BaseTextModelSchema):
    class Meta:
        model = EnumerationValue

    enumeration_id = fields.Integer()