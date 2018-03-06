import base64
import functools
import logging
from typing import Callable

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import Unauthorized

from config import IDM_WEBHOOK_PASSWORD, IDM_WEBHOOK_USERNAME
from customerio.client import customerio
from idm.models import IDMResponse
from user.state import INFO_DECLINED, INFO_NOT_VERIFIED, INFO_PENDING_VERIFICATION, INFO_VERIFIED
from user.verifications import apply_response

log = logging.getLogger(__name__)
blueprint = Blueprint('idm', __name__)


def idm_auth(func: Callable) -> Callable:
    @functools.wraps(func)
    def inner(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            raise Unauthorized()

        token = auth[6:]
        if not token:
            raise Unauthorized()

        if token != base64.b64encode(bytes(f'{IDM_WEBHOOK_USERNAME}:{IDM_WEBHOOK_PASSWORD}', 'ascii')).decode('ascii'):
            raise Unauthorized()

        return func(*args, **kwargs)

    return inner


@blueprint.route('/v1/idm', methods=['POST'])
@idm_auth
def idm_webhook():
    json = request.get_json(force=True)
    log.info(json)
    response = IDMResponse.from_response(json)

    if response.user:
        info_states = [INFO_NOT_VERIFIED, INFO_PENDING_VERIFICATION, INFO_VERIFIED, INFO_DECLINED]
        customerio.event(response.user, 'idm-webhook')
        apply_response(response.user, response, response.user.state in info_states)

    return jsonify({'status': 'ok'})
