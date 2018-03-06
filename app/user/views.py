from flask import Blueprint, jsonify, request
from voluptuous import All, Any, Coerce, Email, Length, Optional, REMOVE_EXTRA, Range, datetime, re
from werkzeug.exceptions import NotFound

from config import ETH_ADDRESS, WHITELISTED_ADDRESSES, WHITELIST_CLOSED, WHITELIST_OPEN_DATE, ETH_MAX_CONTRIBUTION
from errors import ValidationError, WhitelistClosed
from schema import Schema
from user.auth import authenticate
from user.models import User
from user.state import INFO_NOT_VERIFIED
from user.verifications import verify_info

blueprint = Blueprint('info', __name__)


def to_eth(value: str) -> str:
    match = re.match('^(0x)?(?P<addr>[0-9a-f]{40})$', value, flags=re.IGNORECASE)
    if not match:
        raise ValueError(value)
    return match.group('addr').lower()


def to_datetime(value: str) -> datetime.datetime:
    try:
        return datetime.datetime.utcfromtimestamp(int(value))
    except:
        raise ValueError(value)


def to_telegram(value: str) -> str:
    match = re.match('^@?(?P<name>[0-9a-z_]{5,25})$', value, flags=re.IGNORECASE)
    if not match:
        raise ValueError(value)
    return match.group('name')


@blueprint.route('/v1/user', methods=['POST'])
def provide_info():
    if WHITELIST_CLOSED:
        raise WhitelistClosed()

    if WHITELIST_OPEN_DATE and WHITELIST_OPEN_DATE > datetime.datetime.utcnow():
        raise WhitelistClosed(details=dict(open_ts=int(WHITELIST_OPEN_DATE.strftime('%s'))))

    schema = Schema({
        'first_name': All(Length(2, 30), str),
        'last_name': All(Length(2, 30), str),
        'email': Email(),
        'dob': Coerce(to_datetime),
        'address': All(Length(1, 100), str),
        'city': All(Length(2, 30), str),
        Optional('state_code', default=None): Any(None, All(Length(0, 30), str)),
        'zip_code': All(Length(2, 20), str),
        'country_code': All(Length(2, 3), str),
        'phone': All(Length(8, 20), str),
        Optional('eth_address', default=None): Coerce(to_eth),
        Optional('eth_amount', default=None): All(Range(0, 100), Any(float, int)),
        'telegram': Coerce(to_telegram),
        'confirmed_location': bool,
        'dfp': All(Length(10, 4096), str),
        Optional('medium', default=None): Any(None, All(Length(0, 150), str)),
        Optional('reddit', default=None): Any(None, All(Length(0, 150), str)),
        Optional('twitter', default=None): Any(None, All(Length(0, 150), str)),
        Optional('linkedin', default=None): Any(None, All(Length(0, 150), str)),
        Optional('facebook', default=None): Any(None, All(Length(0, 150), str)),
    }, extra=REMOVE_EXTRA, required=True)
    data = schema(request.json)
    data['email'] = data['email'].lower()

    if not data['confirmed_location']:
        raise ValidationError('Unconfirmed location')

    data['ip'] = request.remote_addr
    data['ip_country'] = request.headers.get('CF-IPCountry')

    # Try to find existing user
    user = User.objects(eth_address=data['eth_address']).first()
    if user:
        return jsonify(user.to_json())

    ####################### WHITELIST IS CLOSED FOR NEW USERS ####################
    raise WhitelistClosed()

    user = User.create(**data)

    status = user.transition(INFO_NOT_VERIFIED)

    if status == INFO_NOT_VERIFIED:
        verify_info(user)

    return jsonify(user.reload().to_json()), 201


@blueprint.route('/v1/tokensale/<addr>', methods=['GET'])
def address_is_whitelisted(addr: str):
    if datetime.datetime.utcnow() < datetime.datetime(2018, 2, 21, 7, 0, 0, 0, tzinfo=None):
        raise NotFound()
    try:
        addr = to_eth(addr)
    except ValueError:
        raise NotFound()

    if addr in WHITELISTED_ADDRESSES:
        return jsonify({"address": ETH_ADDRESS, 'max_contribution': ETH_MAX_CONTRIBUTION})
    else:
        raise NotFound()


@blueprint.route('/v1/user', methods=['GET'])
@authenticate(bypass_closing=True)
def get_public_info(user: User):
    return jsonify(user.to_json())


@blueprint.route('/v1/user/<addr>', methods=['GET'])
def get_info_by_eth(addr: str):
    try:
        addr = to_eth(addr)
    except ValueError:
        return jsonify({'status': 'not-found'})

    user = User.objects(eth_address=addr).first()
    if not user:
        return jsonify({'status': 'not-found'})

    status = {
        'clear': 'approved',
        'consider': 'declined'
    }
    return jsonify({
        'status': status.get(user.onfid_status, 'declined'),
    })


@blueprint.route('/v1/status', methods=['GET', 'POST'])
def whitelist_status():
    needs_closed = request.args.get('close')
    if needs_closed or WHITELIST_CLOSED or (WHITELIST_OPEN_DATE and WHITELIST_OPEN_DATE > datetime.datetime.utcnow()):
        raise WhitelistClosed()

    return jsonify({'status': 'open'})
