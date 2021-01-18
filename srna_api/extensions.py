from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_marshmallow import Marshmallow
from flask_oidc import OpenIDConnect
from sqlalchemy.ext.declarative import declarative_base
from srna_api import srna_factory

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
oidc = OpenIDConnect()
Base = declarative_base()

app = srna_factory.create_app(__name__)
celery = srna_factory.make_celery(app)