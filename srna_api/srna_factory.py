import json
from flask import jsonify
from werkzeug.routing import RequestRedirect
from srna_api.decorators.crossorigin import crossdomain
from celery import Celery
#from flask_cors import CORS
from flask_sse import sse

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['result_backend'],
        broker=app.config['broker_url']
    )
    celery.conf.update(app.config)
    celery.conf.task_track_started = True
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def create_app(package_name):
    from flask import Flask
    app = Flask(package_name)
    from srna_api.extensions import db, ma, migrate, oidc
    #cors = CORS(app, resources={r"*": {"origins": "*"}})

    with open('client_secrets.json') as client_secrets_file:
        client_secrets = json.load(client_secrets_file)

    app.config['SQLALCHEMY_DATABASE_URI'] = client_secrets.get('postgres').get('database_uri')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['USE_X_SENDFILE'] = True
    app.config['REDIS_URL'] = 'redis://localhost:6379'

    app.config.update({
        'SECRET_KEY': client_secrets.get('web').get('client_secret'),
        'TESTING': True,
        'DEBUG': True,
        'OIDC_OPENID_REALM': client_secrets.get('web').get('realm'),
        'OIDC_CLIENT_SECRETS': 'client_secrets.json',
        'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
        'OIDC_TOKEN_TYPE_HINT': 'access_token',
        'OIDC_ID_TOKEN_COOKIE_SECURE': False,
        'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    })

    app.config.update(
        broker_url='redis://localhost:6379',
        result_backend='redis://localhost:6379'
    )

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    oidc.init_app(app)

    @app.route('/favicon.ico')
    def favi():
        return 'Hello FaviTown', 200

    return app

def register_blueprints(app):
    from srna_api.web.views import srna_bp
    app.register_blueprint(srna_bp, url_prefix='/srna_api')
    app.register_blueprint(sse, url_prefix='/srna_api/stream')
    return app
