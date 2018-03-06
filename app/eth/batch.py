import json
import logging
import sys
from typing import Tuple

import requests
from mongoengine import QuerySet

from app import create_app
from chunks import chunks
from eth.models import Address
from onfid.helpers import rate_limit
from user.models import User

_ = create_app('prod')
log = logging.getLogger(__name__)


def get_users(start: int = None, limit: int = None) -> QuerySet:
    res = User.objects.order_by('id')
    if start:
        res = res.skip(start)
    if limit:
        res = res.limit(limit)

    return res.no_cache()


@rate_limit(500)
def check_eth(address: str) -> Tuple[float, int]:
    try:
        res = requests.get(
            'https://api.infura.io/v1/jsonrpc/mainnet/eth_getBalance',
            params={'params': json.dumps([f'0x{address}', 'latest'])},
        )
        value = res.json().get('result')
        int_value = int(value, 16)
        balance = float(int_value / (10 ** 18))
    except Exception as ex:
        log.exception('eth_getBalance: %s', ex)
        balance = 0.

    try:
        res = requests.get(
            'https://api.infura.io/v1/jsonrpc/mainnet/eth_getTransactionCount',
            params={'params': json.dumps([f'0x{address}', 'latest'])},
        )
        value = res.json().get('result')
        txes = int(value, 16)
    except Exception as ex:
        log.exception('eth_getBalance: %s', ex)
        txes = 0

    return balance, txes


def check_user(user: User) -> bool:
    eth = user.eth_address
    stored = Address.objects(address=eth).first()
    if not stored:
        balance, txes = check_eth(eth)
        stored = Address(address=eth, balance=balance, transactions=txes).save()
        log.info('User %s has balance of %s and %s transactions', user.id, balance, txes)
    else:
        log.info('User %s has balance of %s and %s transactions [CACHED]', user.id, stored.balance, stored.transactions)
    return stored.balance and stored.transactions


def main(start: int, stop: int):
    users = get_users(start, stop)

    for chunk in chunks(users, 100):
        for user in chunk:
            check_user(user)


if __name__ == '__main__':
    start = count = 0
    if len(sys.argv) == 3:
        start = int(sys.argv[1])
        count = int(sys.argv[2])
    elif len(sys.argv) == 2:
        start = int(sys.argv[1])

    log.info('Doing items %s to %s', start, start + count)
    main(start, count)
