import datetime
import functools
import json
import logging
from typing import Tuple

import requests
from flask import Blueprint, jsonify

from config import DOCK_PER_ETH, ETH_ADDRESS, ETH_BALANCE_ADDRESS
from customerio.client import customerio
from eth.models import Cache
from user.models import User
from user.state import CONTRIBUTED
from user.views import to_eth

ETH_CACHE_KEY = 'eth_amount'
ETH_LAST_TRANSACTION = 'eth_last_transaction'

log = logging.getLogger(__name__)
blueprint = Blueprint('eth', __name__)


def get_amount() -> float:
    if not ETH_BALANCE_ADDRESS:
        return 0

    data = {'params': json.dumps([ETH_BALANCE_ADDRESS, 'latest'])}
    try:
        res = requests.get('https://api.infura.io/v1/jsonrpc/mainnet/eth_getBalance', params=data)
        value = res.json().get('result')
        int_value = int(value, 16)
        return float(int_value / (10 ** 18))
    except:
        return 0.


@functools.lru_cache(2)
def get_cached_amount(_: int) -> Tuple[float, float, datetime.datetime]:
    last_contribution = 0
    cached_contribution = Cache.find(ETH_LAST_TRANSACTION)
    if cached_contribution:
        last_contribution = cached_contribution.value

    cached = Cache.find(ETH_CACHE_KEY)
    if not cached or cached.created_at < datetime.datetime.utcnow() - datetime.timedelta(seconds=30):
        amount = get_amount()
        if amount:
            Cache.set(ETH_CACHE_KEY, amount)
        return amount, last_contribution, datetime.datetime.utcnow()
    else:
        return cached.value, last_contribution, cached.created_at


@blueprint.route('/v1/eth', methods=['GET'])
def eth_amount():
    ts = int(datetime.datetime.utcnow().strftime('%s'))
    amount, last_amount, cache_date = get_cached_amount(int(ts / 30))  # Hack to cache data for 5 minutes
    return jsonify({
        'amount': amount,
        'updated_at': int(cache_date.strftime('%s')),
        'last_amount': last_amount,
    })


@blueprint.route('/v1/check_contributions', methods=['GET'])
def check_contributions():
    """
    {
      "blockNumber": "1961866",
      "timeStamp": "1469624867",
      "hash": "0x545243f19ede50b8115e6165ffe509fde4bb1abc20f287cd8c49c97f39836efe",
      "nonce": "22",
      "blockHash": "0x9ba94fe0b81b32593fd547c39ccbbc2fc14b1bdde4ccc6dccb79e2a304280d50",
      "transactionIndex": "5",
      "from": "0xddbd2b932c763ba5b1b7ae3b362eac3e8d40121a",
      "to": "0x1bb0ac60363e320bc45fdb15aed226fb59c88e44",
      "value": "10600000000000000000000",
      "gas": "127964",
      "gasPrice": "20000000000",
      "isError": "0",
      "txreceipt_status": "",
      "input": "0x",
      "contractAddress": "",
      "cumulativeGasUsed": "227901",
      "gasUsed": "27964",
      "confirmations": "3140511"
    },

    """
    res = requests.get(
        f'http://api.etherscan.io/api?module=account&action=txlist&address={ETH_ADDRESS}'
        f'&startblock=5120812&endblock=99999999&sort=desc'
    )
    data = res.json()
    result = data.get('result')
    total = updated = 0
    last_amount = 0
    for item in result:
        total += 1

        err = item.get('isError')
        if err != '0':
            continue

        to = item.get('to')
        if not to or to_eth(to) != to_eth(ETH_ADDRESS):
            continue
        sender = to_eth(item.get('from'))

        user = User.objects(eth_address=sender).first()
        if not user:
            continue

        tx = item.get('hash')
        if tx in user.contribution_tx:
            continue

        amount = int(item.get('value')) / (10. ** 18)
        if not amount:
            continue

        if total == 1:
            last_amount = user.contribution_amount

        dock_amount = amount * DOCK_PER_ETH

        user.contribution_amount += amount
        user.contribution_tx.append(tx)
        user.save()
        if user.state != CONTRIBUTED:
            user.transition(CONTRIBUTED)

        customerio.event(
            user,
            'token_purchase',
            eth_amount=amount,
            dock_amount=round(dock_amount, 8),
        )
        updated += 1

    if last_amount:
        Cache.set(ETH_LAST_TRANSACTION, last_amount)

    return jsonify({
        'status': 'ok',
        'total': total,
        'updated': updated,
        'last_amount': last_amount,
    })
