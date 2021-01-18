from flask import request, Response, json
from functools import wraps
from srna_api.extensions import oidc

def authentication(original_func):
    @wraps(original_func)
    def decorator(*args, **kwargs):
        return original_func(*args, **kwargs)
    return decorator
