import datetime
from collections import OrderedDict
from typing import Callable, Dict, List, Type
from urllib.parse import urlencode

import flask.testing
import pytest
from bson import ObjectId
from flask import Flask, Response, json
from mongoengine import Document

from app import create_app
from errors import AppError
from tokens import get_token
from user.models import User


@pytest.fixture(scope='function')
def app() -> Flask:
    yield create_app('testing')

    # DB cleanups after each run
    db = Document._get_db()
    for name in db._collections.keys():
        db._collections[name]._documents = OrderedDict()


class TestClient(object):
    def __init__(self, client: flask.testing.FlaskClient):
        self.client = client

    def send(self, method: str, url: str, query: Dict = None, data: Dict = None, auth: str = None,
             **headers) -> Response:
        if auth:
            headers.update({'Authorization': f'Basic {auth}'})
        return self.client.open(
            method=method,
            path=url,
            query_string=urlencode(query) if query else None,
            content_type='application/json',
            data=json.dumps(data),
            headers=headers,
        )

    def delete(self, url: str, query: Dict = None, data: Dict = None, auth: str = None, **headers) -> flask.Response:
        return self.send('DELETE', url, query=query, data=data, auth=auth, **headers)

    def get(self, url: str, query: Dict = None, data: Dict = None, auth: str = None, **headers) -> flask.Response:
        return self.send('GET', url, query=query, data=data, auth=auth, **headers)

    def post(self, url: str, data: Dict = None, query: Dict = None, auth: str = None, **headers) -> flask.Response:
        return self.send('POST', url, query=query, data=data, auth=auth, **headers)

    def put(self, url: str, data: Dict = None, query: Dict = None, auth: str = None, **headers) -> flask.Response:
        return self.send('PUT', url, query=query, data=data, auth=auth, **headers)


@pytest.fixture
def service(client: flask.testing.FlaskClient) -> TestClient:
    return TestClient(client)


@pytest.fixture
def read(service: TestClient) -> TestClient:
    return service


def error(response: flask.Response, error: Type[AppError]) -> bool:
    """ Assert that given response is an instance of given error object """
    assert response.status_code == error.code, response.status_code
    assert response.json.get('error') == error.slugify_exception_name(), response.json
    return True


@pytest.fixture()
def user(service) -> User:
    return User(
        email='blap@example.com',
        eth_address='0000000000000000000000000000000000000000',
        telegram='telegram',
        dob=datetime.datetime.utcnow(),
    ).save()


@pytest.fixture
def three_users(service) -> List[User]:
    return [user(service) for _ in range(3)]


@pytest.fixture
def token() -> Callable:
    def inner(user: User = None) -> str:
        return get_token(user.id if user else ObjectId())

    return inner
