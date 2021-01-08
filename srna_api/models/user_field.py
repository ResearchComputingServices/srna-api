from marshmallow import Schema, fields, ValidationError, pre_load
from sqlalchemy import func, ForeignKey, Sequence, Table, Column, Integer
from sqlalchemy.orm import relationship
from srna_api.extensions import db, ma
import datetime

class UserField(db.Model):
    __tablename__ = 'user_field'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    type = db.Column(db.String())
    value = db.Column(db.String())
    user_id = Column(db.Integer(), ForeignKey('user.id'))
    user = relationship("User", back_populates="fields")
    created_datetime = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    def __init__(self, item):
        self.name = item.get('name')
        self.type = item.get('type')
        self.value = item.get('value')
        self.user_id = item.get('user_id')

    def __repr__(self):
        return '<user_field %r>' % self.word

class UserFieldSchema(ma.ModelSchema):
    class Meta:
        model = UserField

    id = fields.Integer(dump_only=True)
    name = fields.String()
    type = fields.String()
    value = fields.String()
    user_id = fields.Integer(dump_only=True)
