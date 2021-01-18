from flask import request, Response, json
from functools import wraps
from srna_api.extensions import oidc

def authentication(original_func):
    @wraps(original_func)
    def decorator(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if auth == None:
            error = {
                "error": "Could not find authentication token"
            }
            return Response(json.dumps(error), 403, mimetype="application/json")
        auth_fragments = auth.split(' ')
        if len(auth_fragments) < 2 or auth_fragments[0] != 'Bearer':
            error = {
                "error": "Authorization header is invalid"
            }
            return Response(json.dumps(error), 403, mimetype="application/json")
        token = auth_fragments[1]
        print(token)
        is_valid = oidc.validate_token(token)
        if not is_valid:
            error = {
                "error": "Authentication token is not valid"
            }
            return Response(json.dumps(error), 401, mimetype="application/json")
        return original_func(*args, **kwargs)
    return decorator
