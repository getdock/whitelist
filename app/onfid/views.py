import logging

from flask import Blueprint, jsonify, request
from werkzeug.routing import ValidationError

from config import ONFIDO_TOKEN
from onfid.models import Check, Report, Webhook

log = logging.getLogger(__name__)
blueprint = Blueprint('onfido', __name__)


@blueprint.route(f'/v1/onfido/{ONFIDO_TOKEN}', methods=['POST'])
def onfido_webhook():
    json = request.get_json(force=True)
    log.info(json)

    response = Webhook.from_response(json.get('payload'))
    if response.resource_type == Webhook.CHECK:
        cls = Check
    elif response.resource_type == Webhook.REPORT:
        cls = Report
    else:
        log.error('Invalid webhook type: %s', response.resource_type)
        raise ValidationError()

    cls.from_href(response.obj.get('href'))

    return jsonify({'status': 'ok'})
