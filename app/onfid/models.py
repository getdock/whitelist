import datetime
import logging

from blinker import Signal
from mongoengine import DateTimeField, DictField, Document, ListField, ReferenceField, StringField

from onfid.api import api, get_href
from user.models import User

log = logging.getLogger(__name__)


class Report(Document):
    meta = {
        'indexes': ['status', 'result', 'name']
    }

    id = StringField(primary_key=True)
    status = StringField()
    name = StringField()
    result = StringField()
    sub_result = StringField()
    raw = DictField()

    on_update = Signal()

    @classmethod
    def from_response(cls, response: dict) -> 'Report':
        values = dict(
            id=response.get('id'),
            status=response.get('status'),
            name=response.get('name'),
            result=response.get('result'),
            sub_result=response.get('sub_result'),
            raw=response,
        )
        try:
            obj = cls(**values).save(force_insert=True)
        except:
            obj = cls.objects(id=values['id']).get()
            obj.modify(**values)
        cls.on_update.send(obj)
        return obj

    @classmethod
    def from_href(cls, href: str) -> 'Report':
        return cls.from_response(get_href(href))


class Check(Document):
    meta = {
        'indexes': ['user', 'status', 'result']
    }
    id = StringField(primary_key=True)
    user = ReferenceField(User)
    status = StringField()
    name = StringField()
    result = StringField()
    sub_result = StringField()
    raw = DictField()

    reports = ListField(StringField())

    on_update = Signal()

    @classmethod
    def from_response(cls, response: dict, user: User = None) -> 'Check':
        reports = response.get('reports')
        values = dict(
            id=response.get('id'),
            status=response.get('status'),
            name=response.get('name'),
            result=response.get('result'),
            sub_result=response.get('sub_result'),
            reports=[itm.get('id') if isinstance(itm, dict) else itm for itm in reports] if reports else [],
            raw=response,
        )

        if user:
            values.update(user=user)

        try:
            obj = cls(**values).save(force_insert=True)
        except:
            obj = cls.objects(id=values['id']).get()
            obj.modify(**values)
        cls.on_update.send(obj)
        return obj

    @classmethod
    def from_href(cls, href: str) -> 'Check':
        return cls.from_response(get_href(href))

    @classmethod
    def create(cls, user: User) -> 'Check':
        data = {
            'type': 'express',
            'reports': [
                {'name': 'watchlist', 'variant': 'full'},
                {'name': 'document'},
            ],
            'async': True,
        }
        check = api.Checks.create(str(user.onfid_id), data)
        log.info('Created check: %s', check.get('id', check))
        return cls.from_response(check, user=user)


class Webhook(Document):
    CHECK = 'check'
    REPORT = 'report'

    resource_type = StringField()
    action = StringField()
    obj = DictField()

    response_data = DictField()
    received_at = DateTimeField(default=datetime.datetime.utcnow)

    on_create = Signal()

    @classmethod
    def from_response(cls, response: dict) -> 'Webhook':
        obj = cls(
            resource_type=response.get('resource_type'),
            action=response.get('action'),
            obj=response.get('object'),
            response_data=response,
        ).save()
        cls.on_create.send(obj)
        return obj
