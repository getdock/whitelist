from typing import Callable

import pytest
from bson import ObjectId
from mock import patch

from conftest import error
from errors import ObjectNotFound, ValidationError
from ids.const import PASSPORT
from ids.models import IDUpload
from upload.models import Upload
from user.errors import InvalidState
from user.models import User
from user.state import ID_NOT_VERIFIED, INFO_VERIFIED


@pytest.fixture
def upload() -> Callable:
    def inner(user: User, **kwargs) -> Upload:
        return Upload.create(
            user=user,
            original_filename=kwargs.get('filename', 'example.jpg'),
            content_type=kwargs.get('content_type', 'image/jpg'),
            size=kwargs.get('size', 5 * 1024),
        )

    return inner


@pytest.fixture
def ids_upload(upload) -> Callable:
    def inner(user: User, **kwargs) -> IDUpload:
        return IDUpload.create(
            user=user,
            upload1=upload(user),
            upload2=upload(user),
            doc_type=PASSPORT,
            doc_country='AU',
            doc_state='',
        )

    return inner


def test_create_package(service, user, token, upload):
    upload1 = upload(user)
    upload2 = upload(user)

    user.transition(INFO_VERIFIED)

    data = {
        'upload1': str(upload1.id),
        'upload2': str(upload2.id),
        'doc_type': PASSPORT,
        'doc_country': 'AU',
        'doc_state': None,
    }
    with patch('upload.models.Upload.stored_size', 500 * 1024):
        res = service.post('/v1/ids', data, auth=token(user))
        assert res.status_code == 201, res.json


def test_invalid_doc_id(service, user, token, upload):
    upload1 = upload(user)
    upload2 = upload(user)

    user.transition(INFO_VERIFIED)

    data = {
        'upload1': str(upload1.id),
        'upload2': str(upload2.id),
        'doc_type': 'TurtlePass',
        'doc_country': 'AU',
        'doc_state': '',
    }
    res = service.post('/v1/ids', data, auth=token(user))
    assert res.status_code == 400


def test_create_package_missing_upload(service, user, token, upload):
    upload1 = upload(user)

    user.transition(INFO_VERIFIED)

    data = {
        'upload1': str(upload1.id),
        'upload2': str(ObjectId()),
        'doc_type': 'PP',
        'doc_country': 'AU',
        'doc_state': None,
    }
    res = service.post('/v1/ids', data, auth=token(user))
    assert error(res, ObjectNotFound)


def test_invalid_state(service, user, token, upload):
    upload1 = upload(user)
    upload2 = upload(user)

    data = {
        'upload1': str(upload1.id),
        'upload2': str(upload2.id),
        'doc_type': 'PP',
        'doc_country': 'AU',
        'doc_state': '',
    }
    res = service.post('/v1/ids', data, auth=token(user))
    assert error(res, InvalidState)


def test_verify_package(service, user, token, ids_upload):
    ids = ids_upload(user)

    user.transition(ID_NOT_VERIFIED)

    with patch('upload.models.Upload.to_base64', return_value='blop'):
        res = service.post(f'/v1/ids/{ids.id}/verify', auth=token(user))
        assert res.status_code == 200, res.json


def test_verify_invalid_image(service, user, token, upload):
    upload1 = upload(user)
    upload2 = upload(user)
    user.transition(INFO_VERIFIED)
    data = {
        'upload1': str(upload1.id),
        'upload2': str(upload2.id),
        'doc_type': 'PP',
        'doc_country': 'AU',
        'doc_state': '',
    }

    with patch('upload.models.Upload.stored_size', 100):
        res = service.post('/v1/ids', data, auth=token(user))
        assert error(res, ValidationError)
