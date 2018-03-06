from contextlib import contextmanager
from typing import Callable

import pytest
import requests_mock
from mock import Mock, patch

from session import build_session
from user.models import User


@pytest.fixture
def customer_request(service) -> Mock:
    with patch('customerio.client.CustomerIO._session') as sess:
        sess.request = Mock()
        yield sess.request


@pytest.fixture
def customer_identify(service) -> Callable:
    @contextmanager
    def inner(user: User, **data) -> requests_mock.Mocker:
        with patch('customerio.client.CustomerIO.session', build_session()):
            with requests_mock.mock() as mock:
                mock.put(
                    f'https://track.customer.io/api/v1/customers/{user.id}',
                    json=data or user.to_json(),
                )
                yield mock

    return inner


@pytest.fixture
def customer_event(service) -> Callable:
    @contextmanager
    def inner(user: User, event_name: str = None, **data) -> requests_mock.Mocker:
        with patch('customerio.client.CustomerIO.session', build_session()):
            with requests_mock.mock() as mock:
                mock.post(
                    f'https://track.customer.io/api/v1/customers/{user.id}/events',
                    json={'name': event_name, 'data': data} if event_name else None
                )
                yield mock

    return inner


class CustomerMock(requests_mock.Mocker):
    def __init__(self, user: User):
        super().__init__()
        self._user = user

    @property
    def identified(self):
        for history in self.request_history:
            if f'https://track.customer.io/api/v1/customers/{self._user.id}' == history.url:
                return True
        return False

    def has_event(self, event_name: str, data: dict = None):
        for history in self.request_history:
            if f'https://track.customer.io/api/v1/customers/{self._user.id}/events' != history.url:
                continue
            body = history.json()
            if body.get('name') != event_name:
                continue

            if data and body.get('data'):
                if data == body.get('data'):
                    return True
        return False


@pytest.fixture
def customer(service) -> Callable:
    @contextmanager
    def inner(user: User) -> CustomerMock:
        with patch('customerio.client.CustomerIO.session', build_session()):
            with CustomerMock(user) as mock:
                mock.post(f'https://track.customer.io/api/v1/customers/{user.id}/events')
                mock.put(f'https://track.customer.io/api/v1/customers/{user.id}')
                yield mock

    return inner
