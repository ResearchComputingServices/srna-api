from marshmallow import Schema, fields, ValidationError, pre_load
from srna_api.extensions import db, ma
import datetime

class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    created_datetime = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    def __init__(self, item):
        self.id = item.get('id')
        self.name = item.get('name')


    def __repr__(self):
        return '<base_model %r>' % self.id

class BaseModelSchema(ma.ModelSchema):
    id = fields.Integer(dump_only=True)
    name = fields.String()



