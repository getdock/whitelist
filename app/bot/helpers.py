import logging
from functools import wraps

import requests
import telegram

from config import TELEGRAM_ADMINS, TELEGRAM_TOKEN

log = logging.getLogger(__name__)


def register_webhook(baseurl: str, append_token=True) -> requests.Response:
    return requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook',
        json={
            'url': f'{baseurl}{TELEGRAM_TOKEN if append_token else ""}',
        }
    )


def get_webhook_info() -> dict:
    return requests.get(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo').json()


def restricted(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        if user_id not in TELEGRAM_ADMINS:
            log.error("Unauthorized access denied for %s in channel %s.", user_id, chat_id)
            return
        return catch_error(func)(bot, update, *args, **kwargs)

    return wrapped


def catch_error(func):
    @wraps(func)
    def wrapper(bot, update, *args, **kwargs):
        try:
            func(bot, update, *args, **kwargs)
        except Exception as ex:
            log.exception(ex)
            update.message.reply_text(
                f"Snap! bad thing just happened:\n> {ex}",
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

    return wrapper
