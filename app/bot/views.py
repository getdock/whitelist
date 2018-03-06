import logging

from flask import Blueprint, jsonify, request
from telegram import Update

from bot.client import bot, dispatcher
from config import TELEGRAM_TOKEN

log = logging.getLogger(__name__)
blueprint = Blueprint('bot', __name__)


@blueprint.route(f'/v1/bot/{TELEGRAM_TOKEN}', methods=['POST'])
def handle_update():
    update = Update.de_json(request.json, bot)
    dispatcher.process_update(update)
    return jsonify({'status': 'ok'})
