import json
from flask import jsonify
from werkzeug.routing import RequestRedirect
from srna_api.decorators.crossorigin import crossdomain
from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

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

    with open('client_secrets.json') as client_secrets_file:
        client_secrets = json.load(client_secrets_file)

    app.config['SQLALCHEMY_DATABASE_URI'] = client_secrets.get('postgres').get('database_uri')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['USE_X_SENDFILE'] = True

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
        #'KEYCLOAK_USERNAME' : client_secrets.get('web').get('keycloak_username')
    })

    app.config.update(
        CELERY_BROKER_URL='redis://localhost:6379',
        CELERY_RESULT_BACKEND='redis://localhost:6379'
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
    return app