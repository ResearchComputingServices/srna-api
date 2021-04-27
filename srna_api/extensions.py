from flask_oidc import OpenIDConnect


oidc = OpenIDConnect()


from srna_api.srna_factory import create_app, make_celery

app = create_app(__name__)
celery = make_celery(app)