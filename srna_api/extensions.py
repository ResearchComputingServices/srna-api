from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_marshmallow import Marshmallow
from flask_oidc import OpenIDConnect
from sqlalchemy.ext.declarative import declarative_base
from srna_api.srna_factory import create_app

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
oidc = OpenIDConnect()
Base = declarative_base()

app = create_app(__name__)
