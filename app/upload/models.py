import base64
import datetime
import logging
import mimetypes

from blinker import Signal
from mongoengine import DateTimeField, Document, IntField, ReferenceField, StringField

from upload.s3 import s3
from user.models import User

log = logging.getLogger(__name__)

PUT_URL_DEFAULT_EXPIRE = 60 * 60 * 24 * 7


class Upload(Document):
    PUBLIC_FIELDS = ['id', 'content_type', 'size', 'original_filename', 'url']

    meta = {
        'indexes': ['user'],
    }

    user = ReferenceField(User, required=True)
    content_type = StringField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    original_filename = StringField()
    size = IntField()
    url = StringField()
    put_url = StringField()

    on_create = Signal()

    @property
    def url(self):
        return s3.sign_url(
            filename=self.filename,
            method='GET',
            expire=60 * 60 * 24 * 365,  # 1Y
        )

    @property
    def filename(self):
        return f'{self.user.id}/{self.id}{"." if self.extension else ""}{self.extension}'

    @property
    def extension(self):
        if '.' in self.original_filename:
            return self.original_filename.rsplit('.', 1)[-1]
        else:
            return None

    @property
    def put_url(self):
        headers = {
            'Content-Type': self.content_type,
            'Content-Disposition': f'attachment; filename={self.filename}',
        }

        return s3.sign_url(
            filename=self.filename,
            headers=headers,
            method='PUT',
            expire=PUT_URL_DEFAULT_EXPIRE,
        )

    @classmethod
    def create(cls, user: User, original_filename: str, content_type: str = None, size: int = None, **kwargs):
        if not content_type:
            content_type, _ = mimetypes.guess_type(original_filename)
        upload = cls(
            original_filename=original_filename,
            content_type=content_type,
            size=size,
            user=user,
            **kwargs
        ).save()
        cls.on_create.send(upload)
        return upload

    @staticmethod
    def upload(data: bytes, filename: str, content_type: str) -> str:
        headers = {'Content-Disposition': f'attachment; filename={filename}'}
        return s3.put(
            filename,
            data,
            content_type=content_type,
            **headers
        )

    def to_base64(self) -> str:
        data = s3.get(self.filename)
        b64 = base64.b64encode(data).decode('ascii')
        return f'{self.content_type};base64,{b64}'

    @property
    def stored_size(self):
        """ Return size in bytes of the file stored on s3. This is more reliable than data provided by user. """
        return s3.file_size(self.filename)

    @property
    def fh(self):
        return s3.key(self.filename)