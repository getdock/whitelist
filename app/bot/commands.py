import datetime
from io import StringIO

import gevent
import telegram
from bson import ObjectId
from mongoengine import Q
from telegram.ext import CommandHandler

from bot.client import dispatcher
from bot.helpers import restricted
from control import export
from ids.models import IDUpload
from onfid.models import Check
from upload.models import Upload
from upload.s3 import s3
from user.models import User
from user.state import ALL_STATES
from user.views import to_eth

status_message = """Users by states:
{states}

Users by kyc verification result:
{kycs}

Users submitted their IDs: <b>{uploads}</b>

Users by ID verification:
{ids}
"""

onfido_message = """
Number of attempted users: <b>{users}</b>
Number of created checks: <b>{checks}</b>
Number of processed checks: <b>{completed} ({completed_percent:.3}%)</b>

Users by results:
{results}
"""


@restricted
def status(_: telegram.Bot, update: telegram.Update):
    states = User.objects.aggregate({'$group': {'_id': '$state', 'count': {'$sum': 1}}})
    kyc = User.objects.aggregate({'$group': {'_id': '$kyc_result', 'count': {'$sum': 1}}})
    idm = User.objects.aggregate({'$group': {'_id': '$idm_result', 'count': {'$sum': 1}}})
    uploads = IDUpload.objects.count()

    update.message.reply_text(
        status_message.format(
            states='\n'.join(f'* <b>{item["_id"]}</b>: {item["count"]}' for item in states),
            kycs='\n'.join(f'* <b>{item["_id"]}</b>: {item["count"]}' for item in kyc),
            ids='\n'.join(f'* <b>{item["_id"]}</b>: {item["count"]}' for item in idm),
            uploads=uploads,
        ),
        parse_mode=telegram.ParseMode.HTML,
        quote=False,
    )


@restricted
def onfido(_: telegram.Bot, update: telegram.Update):
    states = User.objects.aggregate({'$group': {'_id': '$onfid_status', 'count': {'$sum': 1}}})
    count = User.objects(onfid_id__ne=None).count()
    checks = Check.objects.count()

    res = {item['_id']: item['count'] for item in states if item['_id']}
    completed = sum(res.values())

    update.message.reply_text(
        onfido_message.format(
            results='\n'.join(f'* <b>{key}</b>: {value} ({value/completed*100.:.3}%)' for key, value in res.items()),
            completed=completed,
            completed_percent=float(completed / checks * 100.),
            checks=checks,
            users=count,
        ),
        parse_mode=telegram.ParseMode.HTML,
        quote=False,
    )


@restricted
def countries(_: telegram.Bot, update: telegram.Update):
    agg = User.objects.aggregate({'$group': {'_id': '$country_code', 'count': {'$sum': 1}}})
    values = [
        (item['_id'], item['count'])
        for item in sorted(agg, key=lambda x: x['count'], reverse=True)
    ]

    update.message.reply_text(
        "\n".join([f'* <b>{key}</b>: {value}' for key, value in values[:15]]),
        parse_mode=telegram.ParseMode.HTML,
        quote=False,
    )


@restricted
def count(_: telegram.Bot, update: telegram.Update):
    users = User.objects.count()
    update.message.reply_text(
        f'There are *{users}* registered users!',
        parse_mode=telegram.ParseMode.MARKDOWN,
        quote=False,
    )


@restricted
def do_export(_: telegram.Bot, update: telegram.Update, args: list = None):
    state = args[0] if args else None

    if state and state not in ALL_STATES:
        update.message.reply_text(
            f'Invalid state. Possible values are: {", ".join(ALL_STATES)}'
        )
        return

    if update.effective_chat.id != update.effective_user.id:
        update.message.reply_text('Please send this command directly to bot (in a private channel)')
        return

    gevent.spawn(export_async, update, state)


def export_async(update: telegram.Update, state: str):
    now = datetime.datetime.utcnow().isoformat()
    filename = f'Export.{now}.{ObjectId()}.csv'
    signed_url = s3.sign_url(filename, method='GET', expire=1800)

    with StringIO() as fh:
        export_count = export(fh, state=state)
        fh.seek(0)

        Upload.upload(fh.read(), filename, 'text/csv')
        update.message.reply_text(
            f'Exported *{export_count}* users to {signed_url}',
            parse_mode=telegram.ParseMode.MARKDOWN,
            quote=False,
        )


@restricted
def info(_: telegram.Bot, update: telegram.Update, args: list = None):
    if not args:
        update.message.reply_text("Please provide user id")
        return

    try:
        user = User.objects(id=ObjectId(args[0])).first()
    except:
        try:
            user = User.objects(eth_address=to_eth(args[0])).first()
        except:
            user = User.objects(Q(email=args[0]) | Q(telegram=args[0])).first()

    if not user:
        update.message.reply_text(
            "I wasn't able to find such user",
            parse_mode=telegram.ParseMode.HTML,
            quote=True,
        )
        return

    update.message.reply_text(
        "\n".join([
            f'<b>{key}</b>: {value}'
            for key, value in user.to_csv().items()
        ]),
        parse_mode=telegram.ParseMode.HTML,
        quote=True,
    )


handlers = [
    CommandHandler('count', count),
    CommandHandler('countries', countries),
    CommandHandler('status', status),
    CommandHandler('onfido', onfido),
    CommandHandler('export', do_export, pass_args=True),
    CommandHandler('info', info, pass_args=True),
]

for handler in handlers:
    dispatcher.add_handler(handler)
