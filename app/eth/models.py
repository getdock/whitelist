import datetime
from typing import Any, Union

from mongoengine import DateTimeField, Document, DynamicField, StringField, FloatField, BooleanField, IntField


class Cache(Document):
    meta = {
        'indexes': [
            {'fields': ['created_at'], 'expireAfterSeconds': 600},
        ]
    }
    key = StringField(primary_key=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    value = DynamicField()

    @classmethod
    def find(cls, key: str) -> Union[None, 'Cache']:
        result = cls.objects(key=key).first()
        if result:
            return result
        return None

    @classmethod
    def set(cls, key: str, value: Any):
        cls.objects(key=key).update(
            value=value,
            created_at=datetime.datetime.utcnow(),
            upsert=True,
        )


class Address(Document):
    address = StringField(primary_key=True)

    balance = FloatField()
    transactions = IntField()
    valid = BooleanField()

    comment = StringField()