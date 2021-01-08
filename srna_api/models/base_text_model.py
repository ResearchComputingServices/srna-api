from marshmallow import Schema, fields, ValidationError, pre_load
from srna_api.extensions import db, ma
import datetime

class BaseTextModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String())
    created_datetime = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    def __init__(self, item):
        self.id = item.get('id')
        self.text = item.get('text')

    def __repr__(self):
        return '<base_model %r>' % self.id

class BaseTextModelSchema(ma.ModelSchema):
    id = fields.Integer(dump_only=True)
    text = fields.String()


