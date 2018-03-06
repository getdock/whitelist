from typing import Tuple

from blinker import Signal
from mongoengine import DateTimeField, Document, ReferenceField, StringField

from ids.const import DOC_TYPES
from upload.models import Upload
from user.models import User


class IDUpload(Document):
    user = ReferenceField(User, required=True)
    upload1 = ReferenceField(Upload, required=True)
    upload2 = ReferenceField(Upload, required=True)

    # TODO: Validate doc_country
    doc_type = StringField(required=True, choices=DOC_TYPES)
    doc_country = StringField(required=True)
    doc_state = StringField()

    created_at = DateTimeField()
    submitted_at = DateTimeField()
    verified_at = DateTimeField()
    status = StringField()  #: Verification status

    on_create = Signal()
    on_verification_started = Signal()
    on_verification_completed = Signal()

    @classmethod
    def create(cls, user: User, upload1: Upload, upload2: Upload, doc_type: str, doc_country: str,
               doc_state: str) -> 'IDUpload':
        obj = cls(
            doc_country=doc_country,
            doc_state=doc_state,
            doc_type=doc_type,
            upload1=upload1,
            upload2=upload2,
            user=user,
        ).save(force_insert=True)
        cls.on_create.send(obj)
        return obj

    def verify(self) -> Tuple[bool, str]:
        # idm.verify_ids()
        return True, 'blop'

    def to_json(self):
        return {
            'id': str(self.id),
            'upload1': str(self.upload1.id) if self.upload1 else None,
            'upload2': str(self.upload2.id) if self.upload2 else None,
            'doc_type': self.doc_type,
            'doc_country': self.doc_country,
            'doc_state': self.doc_state,
            'created_at': int(self.created_at.strftime('%s')) if self.created_at else None,
            'submitted_at': int(self.submitted_at.strftime('%s')) if self.submitted_at else None,
            'verified_at': int(self.verified_at.strftime('%s')) if self.verified_at else None,
            'status': self.status,
        }
