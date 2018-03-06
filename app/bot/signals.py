import telegram

from bot.client import bot
from config import TELEGRAM_ADMIN_CHANNEL, TELEGRAM_PUBLIC_CHANNEL
from idm.models import IDMResponse
from signals import Transition, connect, transition, log_exception
from user.models import User
from user.state import ID_DECLINED, ID_FAILED, ID_VERIFIED, INFO_FAILED, INFO_NOT_VERIFIED


# @transition(None, ID_VERIFIED)
@log_exception
def public_stats_announcements(user: User, transition: Transition):
    if not TELEGRAM_PUBLIC_CHANNEL:
        return

    count = User.objects(state=ID_VERIFIED).count()
    if count % 1000:
        bot.send_message(
            TELEGRAM_PUBLIC_CHANNEL,
            f"We've reached *{count}* verified users!",
            parse_mode=telegram.ParseMode.MARKDOWN,
        )


# @transition(None, INFO_NOT_VERIFIED)
@log_exception
def new_user_registered(user: User, transition: Transition):
    if not TELEGRAM_ADMIN_CHANNEL:
        return

    bot.send_message(
        TELEGRAM_ADMIN_CHANNEL,
        f"User <b>{user.name} {user.email}[{user.id}]</b> just registered",
        parse_mode=telegram.ParseMode.HTML,
    )


# @transition(None, ID_DECLINED)
@log_exception
def declined_id_verification(user: User, transition: Transition):
    if not TELEGRAM_ADMIN_CHANNEL:
        return

    bot.send_message(
        TELEGRAM_ADMIN_CHANNEL,
        f"User {user} declined ID verification",
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


# @transition(None, ID_FAILED)
@log_exception
def failed_id_verification(user: User, transition: Transition):
    if not TELEGRAM_ADMIN_CHANNEL:
        return

    bot.send_message(
        TELEGRAM_ADMIN_CHANNEL,
        f"Error during ID verification for user {user}",
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


# @transition(None, INFO_FAILED)
@log_exception
def failed_id_verification(user: User, transition: Transition):
    if not TELEGRAM_ADMIN_CHANNEL:
        return

    bot.send_message(
        TELEGRAM_ADMIN_CHANNEL,
        f"Error during info verification for user {user}",
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


@connect(IDMResponse.on_received)
def notify_about_missing_user(response: IDMResponse, **_):
    if not response.user:
        bot.send_message(
            TELEGRAM_ADMIN_CHANNEL,
            f"Response {response.id} ({response.transaction_id}) have no user associated",
            parse_mode=telegram.ParseMode.MARKDOWN,
        )
