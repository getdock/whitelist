import datetime

from mock import patch

from conftest import error
from errors import WhitelistClosed
from tokens import get_token
from user.test_user_info import new_user


def test_valid_token_auth(service, user):
    res = service.get('/v1/user', auth=get_token(user.id))
    assert res.status_code == 200


def test_closed_whitelist(service):
    with patch('user.views.WHITELIST_CLOSED', True):
        res = service.post('/v1/user', new_user())
        assert error(res, WhitelistClosed)


def test_whitelist_not_yet_opened(service):
    ts = datetime.datetime(2020, 10, 10)
    with patch('user.views.WHITELIST_OPEN_DATE', ts):
        res = service.post('/v1/user', new_user())
        assert error(res, WhitelistClosed)
