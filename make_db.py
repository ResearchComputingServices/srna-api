import subprocess
from srna_api.extensions import db, ma
from srna_api import models, providers, srna_factory
import glob
import importlib
import os

app = srna_factory.create_app(__name__)

def is_python_script(name):
    return '.py' in name

def execute_python_script(name, db, models):
    name = name.replace('db_scripts/', '')
    name = name.replace('.py', '')
    if name != '__init__':
        module = importlib.import_module("." + name, 'db_scripts')
        module.populate(db, models, providers)

def execute_sql_script(name, db):
    with open(name) as fn:
        content = fn.read()
        db.session.execute(content)

def populate_db(db):
    db_scripts = sorted(glob.glob('db_scripts/*'))
    db_scripts.sort()
    for name in db_scripts:
        if os.path.isdir(name):
            continue
        if is_python_script(name):
            execute_python_script(name, db, models)
        else:
            execute_sql_script(name, db)
    db.session.commit()

def create_db(db):
    db.engine.execute("drop schema if exists public cascade")
    db.engine.execute("create schema public")
    db.reflect()
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        print('Creating database...')
        create_db(db)
        print('Populating database...')
        populate_db(db)
        print('DONE')
