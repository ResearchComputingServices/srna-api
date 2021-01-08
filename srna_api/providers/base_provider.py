from srna_api.extensions import db, ma
from sqlalchemy import func
from flask import json, request, Response
from sqlalchemy.sql import text

class BaseProvider():
    def generate_id(self, offset=0, field=None):
        max_id = db.session.query(func.max(field)).scalar()
        max_id = max_id + 1 if max_id else 1
        return max_id + offset

    def get_count(self, field):
        count = db.session.query(field.id).count()
        dict = {"count": count}
        response = Response(json.dumps(dict), 200, mimetype="application/json")
        return response

    def query_all(self, field):
        query = field.query
        limit = request.args.get('limit')
        offset = request.args.get('offset')

        #default values
        column = 'id'
        order = 'asc'

        if 'column' in request.args:
            column = request.args.get('column')

        if 'order' in request.args:
            order = request.args.get('order')

        p = column + ' ' + order

        query = query.order_by(text(p))
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        result = query.all()

        return result

    def query_all_by_subquery_original(self, query):
        limit = request.args.get('limit')
        offset = request.args.get('offset')

        #default values
        column = 'id'
        order = 'asc'

        if 'column' in request.args:
            column = request.args.get('column')

        if 'order' in request.args:
            order = request.args.get('order')

        p = column + ' ' + order
        query = query.order_by(text(p))

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        result = query.all()
        return result


    def query_all_by_subquery(self, query, model):
        limit = request.args.get('limit')
        offset = request.args.get('offset')

        #default values
        column = model + '_id'
        order = 'asc'

        if 'column' in request.args:
            column = model + '_' + request.args.get('column')

        if 'order' in request.args:
            order = request.args.get('order')

        p = column + ' ' + order
        query = query.order_by(text(p))

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        result = query.all()
        return result




    def add_category_to_data(self, data):
        data_test_category = data.get('test_category')
        if data_test_category:
            data['test_category_id'] = data_test_category['id']
        return data

    def fill_out_name_based_on_display(self, data):
        data['name'] = data.get('display') if data.get('name') is None else data.get('name')
        return data


    def query_filter_by(self, model, filters):
        query = model.query
        limit = request.args.get('limit')
        offset = request.args.get('offset')


        # default values
        column = 'id'
        order = 'asc'

        if 'column' in request.args:
            column = request.args.get('column')

        if 'order' in request.args:
            order = request.args.get('order')

        p = column + ' ' + order

        if limit and offset:
            limit = int(limit)
            offset = int(offset)
            page = int(offset / limit) + 1
            result = query.filter_by(**filters).order_by(text(p)).paginate(page=page, per_page=limit,error_out=False).items
        else:
            result = query.filter_by(**filters).order_by(text(p)).all()

        return result


