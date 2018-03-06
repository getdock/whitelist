from io import BytesIO

from mock import patch

from conftest import error
from errors import ValidationError
from upload.models import Upload


def test_upload(service, user, token):
    data = {
        'filename': 'blop.jpg',
        'content_type': 'image/jpeg',
        'size': 500 * 1024,
    }
    res = service.post('/v1/upload', data, auth=token(user))
    assert res.status_code == 200, res.json

    upload = Upload.objects().get()
    assert upload.user == user
    assert upload.filename == f'{user.id}/{upload.id}.jpg'


def test_base64(user):
    data = BytesIO(b'Hello')
    with patch('upload.s3.s3.get', return_value=data.read()):
        res = Upload(user=user, original_filename='blop', content_type='image/png').to_base64()
        assert res == 'image/png;base64,SGVsbG8='


def test_stored_size(user):
    with patch('upload.s3.S3.file_size', return_value=1234):
        res = Upload(user=user, original_filename='blop', content_type='image/png').stored_size
        assert res == 1234


def test_no_extension(service, user, token):
    data = {
        'filename': 'no_extension',
        'content_type': 'image/jpeg',
        'size': 500 * 1024,
    }
    res = service.post('/v1/upload', data, auth=token(user))
    assert error(res, ValidationError)


def test_invalid_extension(service, user, token):
    data = {
        'filename': 'file.bMp',
        'content_type': 'image/jpeg',
        'size': 500 * 1024,
    }
    res = service.post('/v1/upload', data, auth=token(user))
    assert error(res, ValidationError)
