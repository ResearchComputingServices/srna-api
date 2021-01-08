from srna_api.web.views import *
from srna_api import srna_factory

global app

app = srna_factory.create_app(__name__)
app.app_context().push()
srna_factory.register_blueprints(app)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=7017)

