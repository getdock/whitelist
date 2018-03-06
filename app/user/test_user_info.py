import datetime

import pytest
from mock import patch
from requests import HTTPError, Response

from conftest import error
from errors import ObjectExists, ValidationError
from idm.const import STATUS_ACCEPTED, STATUS_DECLINED, USER_REPUTATION_SUSPICIOUS
from idm.errors import IDMError
from idm.models import IDMResponse
from tokens import get_token
from user.models import User
from user.state import DECLINE_COUNTRY, INFO_DECLINED, INFO_FAILED, INFO_PENDING_VERIFICATION, INFO_VERIFIED
from user.views import to_eth


def new_user(**kwargs) -> dict:
    default = {
        'email': kwargs.get('email', 'user@example.com'),
        'dob': int(datetime.datetime(2010, 10, 10).strftime('%s')),
        'dfp': '{"some":"data", "is": "here"}',
        'phone': '+1234567890',
        'eth_address': kwargs.get('eth_address', '0x29D7d1dd5B6f9C864d9db560D72a247c178aE86B'),
        'eth_amount': 1.23,
        'address': 'blappy blop',
        'city': 'blappy blop',
        'state_code': 'CA',
        'zip_code': '12345',
        'country_code': 'AU',
        'telegram': '@telegram',
        'confirmed_location': True,
        'first_name': 'Homer',
        'last_name': 'Simpson',
    }
    if 'dob' in kwargs:
        kwargs['dob'] = kwargs['dob'].strftime('%s')
    default.update(kwargs)
    return default


def test_to_eth():
    failed = [
        'DEADBEEF',
        '0x12345',
        '0x12345',
    ]
    for item in failed:
        with pytest.raises(ValueError):
            to_eth(item)

    assert to_eth('0x29D7d1dd5B6f9C864d9db560D72a247c178aE86B') == '29D7d1dd5B6f9C864d9db560D72a247c178aE86B'
    assert to_eth('29D7d1dd5B6f9C864d9db560D72a247c178aE86B') == '29D7d1dd5B6f9C864d9db560D72a247c178aE86B'


def test_new_user(service):
    data = new_user()
    res = service.post('/v1/user', data)
    assert res.status_code == 201, res.json

    user = User.objects.get()
    assert user.email == data['email']
    assert user.eth_address == '29D7d1dd5B6f9C864d9db560D72a247c178aE86B'


def test_get_updated_info(service):
    data = new_user()
    res = service.post('/v1/user', data)
    assert res.status_code == 201, res.json
    assert res.json['email'] == data['email']
    assert res.json['dob'] == data['dob']


def test_add_dob(service):
    dt = datetime.datetime(2010, 10, 10)

    res = service.post('/v1/user', new_user(dob=dt))
    assert res.status_code == 201, res.json

    user = User.objects.get()
    assert user.dob == dt


def test_interrupted_verification(service):
    """ Make sure user remains in INFO_PENDING if IDM verification fails. """
    # Raise exception during IDM verification
    with patch('user.verifications.verify', side_effect=Exception):
        with pytest.raises(Exception):
            service.post('/v1/user', new_user())

    user = User.objects.get()
    assert user.state == INFO_PENDING_VERIFICATION


def test_failed_verification_request(service):
    with patch('user.verifications.verify', side_effect=IDMError(HTTPError('blop', response=Response()))):
        service.post('/v1/user', new_user())

    user = User.objects.get()
    assert user.state == INFO_FAILED
    # assert user.info == 'blop'


def test_successful_verification(service):
    with patch('user.verifications.verify', return_value=IDMResponse(result=STATUS_ACCEPTED, transaction_id='123')):
        service.post('/v1/user', new_user())

    user = User.objects.get()
    assert user.state == INFO_VERIFIED


def test_declined_verification(service):
    response = IDMResponse(result=STATUS_DECLINED, transaction_id='123', user_reputation=USER_REPUTATION_SUSPICIOUS)

    with patch('user.verifications.verify', return_value=response):
        service.post('/v1/user', new_user())

    user = User.objects.get()
    assert user.state == INFO_DECLINED
    assert user.info == USER_REPUTATION_SUSPICIOUS


def test_declined_by_pending_verification(service):
    """ Make sure we stop handling IDM if user was declined within INFO_PENDING_VERIFICATION state. """

    def decline_user(user: User, transition):
        """ Decline user as it reaches INFO_PENDING_VERIFICATION state. """
        if transition[1] == INFO_PENDING_VERIFICATION:
            user.transition(INFO_DECLINED)

    with User.on_transition.connected_to(decline_user):
        with patch('idm.verify.verify') as idm_call:
            service.post('/v1/user', new_user())
            idm_call.assert_not_called()

    user = User.objects.get()
    assert user.state == INFO_DECLINED


def test_user_token(service):
    res = service.post('/v1/user', new_user())
    assert res.status_code == 201, res.json

    user = User.objects.get()
    assert res.json['token'] == get_token(user.id)


def test_start_as_existing_user(service, user):
    res = service.post('/v1/user', new_user(email=user.email, eth_address=user.eth_address))
    assert res.status_code == 200, res.json

    # This will be the same user
    assert res.json['id'] == str(user.id)
    assert User.objects.count() == 1


def test_try_using_existing_eth(service, user):
    res = service.post('/v1/user', new_user(email='another@example.com', eth_address=user.eth_address))
    assert error(res, ObjectExists)


def test_try_using_existing_email(service, user):
    res = service.post('/v1/user', new_user(email=user.email, eth_address='0x1111111111111111111111111111111111111111'))
    assert error(res, ObjectExists)


@pytest.mark.skip
def test_banned_country(service):
    with patch('user.verifications.BANNED_COUNTRIES', ['AU']):
        res = service.post('/v1/user', new_user(), **{'CF-IPCountry': 'AU'})
        assert res.status_code == 201
        assert res.json['state'] == INFO_DECLINED
        assert res.json['decline_reason'] == DECLINE_COUNTRY


def test_not_confirmed_location(service):
    res = service.post('/v1/user', new_user(confirmed_location=False))
    assert error(res, ValidationError)


def test_invalid_telegram(service):
    res = service.post('/v1/user', new_user(telegram='no'))
    assert error(res, ValidationError)


def test_two_telegrams(service, user):
    res = service.post('/v1/user', new_user(telegram='telegram'))
    assert error(res, ObjectExists)


def test_missing_eth(service):
    data = new_user()
    data.pop('eth_address')
    res = service.post('/v1/user', data)
    assert res.status_code == 201, res.json
