from marshmallow import Schema, fields, ValidationError, pre_load
from sqlalchemy import func, ForeignKey, Sequence, Table, Column, Integer
from sqlalchemy.orm import relationship
from srna_api.extensions import db, ma
from srna_api.models.base_model import BaseModel, BaseModelSchema
from srna_api.models.mutable_list import MutableList
from sqlalchemy.dialects.postgresql import ARRAY

class Authorization(BaseModel):
    __tablename__='authorization'
    text = db.Column(db.String())
    category = db.Column(db.String())
    dependencies = db.Column(
        MutableList.as_mutable(ARRAY(db.String())),
        server_default="{}"
    )

    def __init__(self, item):
        BaseModel.__init__(self,item)
        self.text = item.get('text')
        self.category = item.get('category')
        self.dependencies = item.get('dependencies')


    def __repr__(self):
        return '<authorization %r>'  % self.id


class AuthorizationSchema(BaseModelSchema):
    class Meta:
        model = Authorization

    text = fields.String()
    category = fields.String()
    dependencies = fields.List(fields.String())
