import datetime
import functools
from typing import Callable

from flask import request
from mongoengine import DoesNotExist
from werkzeug.exceptions import Unauthorized

from config import WHITELIST_CLOSED, WHITELIST_OPEN_DATE
from errors import WhitelistClosed
from tokens import verify_token
from user.errors import UserNotFound
from user.models import User


def authenticate(should_exist: bool = True, bypass_closing: bool = False) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        def inner(*args, **kwargs):
            if not bypass_closing and WHITELIST_CLOSED:
                raise WhitelistClosed()

            if not bypass_closing and WHITELIST_OPEN_DATE and WHITELIST_OPEN_DATE > datetime.datetime.utcnow():
                raise WhitelistClosed(details=dict(open_ts=int(WHITELIST_OPEN_DATE.strftime('%s'))))

            auth = request.headers.get('Authorization')
            if not auth:
                raise Unauthorized()

            token = auth[6:]
            if not token:
                raise Unauthorized()

            try:
                user_id = verify_token(token)
            except ValueError:
                raise Unauthorized()

            try:
                user = User.objects(id=user_id).get()
            except DoesNotExist:
                if not should_exist:
                    user = User(id=user_id)
                else:
                    raise UserNotFound()

            return func(*args, user=user, **kwargs)

        return inner

    return wrapper
