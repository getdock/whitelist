import re
from typing import Any

import mongoengine.errors
import voluptuous
from flask import jsonify
from werkzeug.exceptions import HTTPException


class AppError(HTTPException):
    code = 400

    def __init__(self, key: str = None, details: Any = None, code: int = None):
        super(AppError, self).__init__()
        self.key = key
        if code:
            self.code = code
        self.details = details

    @classmethod
    def slugify_exception_name(cls):
        return re.sub(r'(?<=[a-z])(?=[A-Z])', '-', cls.__name__).lower()

    def get_response(self, environ=None):
        return self.jsonify()

    def jsonify(self):
        error_obj = {
            'error': self.slugify_exception_name(),
            'key': self.key,
            'details': self.details,
        }

        res = jsonify(error_obj)
        res.status_code = self.code

        return res


class ObjectExists(AppError):
    pass


class ValidationError(AppError):
    pass


class RouteNotFound(AppError):
    pass


class ObjectNotFound(AppError):
    code = 404
    pass


class WhitelistClosed(AppError):
    code = 410


def register_errors(app):
    @app.errorhandler(AppError)
    def handle_invalid_usage(error):
        return error.jsonify()

    @app.errorhandler(mongoengine.errors.NotUniqueError)
    def handle_duplicate_object(error):
        return ObjectExists().jsonify()

    @app.errorhandler(mongoengine.errors.DoesNotExist)
    def handle_missing_object(error):
        return ObjectNotFound().jsonify()

    @app.errorhandler(404)
    def route_not_found_error(error):
        return RouteNotFound().jsonify()

    @app.errorhandler(voluptuous.Invalid)
    def route_validation_error(error):
        return ValidationError(str(error)).jsonify()
