from bson import ObjectId
from werkzeug.routing import BaseConverter, ValidationError

import bot.views
import eth.views
import idm.views
import ids.views
import onfid.views
import upload.views
import user.views
from tokens import get_token, verify_token


def load_blueprints():
    return [
        eth.views.blueprint,
        ids.views.blueprint,
        idm.views.blueprint,
        onfid.views.blueprint,
        bot.views.blueprint,
        user.views.blueprint,
        upload.views.blueprint,
    ]


class TokenConverter(BaseConverter):

    def to_python(self, value: str) -> ObjectId:
        try:
            return verify_token(value)
        except ValueError:
            raise ValidationError(value)

    def to_url(self, value: ObjectId) -> str:
        return get_token(value)
