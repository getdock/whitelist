import datetime
import logging

from blinker import Signal
from bson import ObjectId
from mongoengine import DateTimeField, DictField, Document, IntField, ReferenceField, StringField
from requests import HTTPError

from config import IDM_PASSWORD, IDM_URL, IDM_USERNAME
from idm.const import STATUS_PENDING
from idm.errors import IDMError
from idm.helpers import build_request, parse_response
from session import build_session
from user.models import User

log = logging.getLogger(__name__)
session = build_session(1024)
session.auth = (IDM_USERNAME, IDM_PASSWORD)


class IDMRequest(Document):
    """ Keeps track of all KYC requests we've performed to the IDM. """

    meta = {
        'indexes': ['user', 'transaction_id'],
    }

    user = ReferenceField(User, required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    requested_at = DateTimeField()

    #: Transaction id for the same user must be the same (when user goes from first to second stage)
    transaction_id = StringField(default=lambda: str(ObjectId()), unique=True)

    request_data = DictField()
    response_status = IntField()

    on_create = Signal()

    @classmethod
    def create(cls, user: User, **data) -> 'IDMRequest':
        body = build_request(user, **data)
        obj = cls(
            user=user,
            request_data=body,
            transaction_id=body['tid'],
        ).save()
        cls.on_create.send(obj)
        return obj

    def request(self) -> 'IDMResponse':
        if not IDM_USERNAME:
            return IDMResponse.empty()

        try:
            res = session.request('POST', IDM_URL, json=self.request_data)
            self.update(
                requested_at=datetime.datetime.utcnow(),
                response_status=res.status_code,
            )

            if res.status_code != 200:
                raise HTTPError(res.text, response=res)
            return IDMResponse.from_response(res.json())
        except HTTPError as err:
            log.exception('IDM request error: %s', err)
            raise IDMError(err)


class IDMResponse(Document):
    """ Keeps track of all responses we've received from the IDM. """

    meta = {
        'indexes': ['user', 'transaction_id'],
    }

    user = ReferenceField(User)
    received_at = DateTimeField(default=datetime.datetime.utcnow)

    transaction_id = StringField(required=True)
    result = StringField()
    kyc_state = StringField()
    user_reputation = StringField()
    fraud_result = StringField()
    previous_reputation = StringField()

    response_data = DictField()

    on_received = Signal()

    @property
    def status(self):
        return self.result or self.kyc_state or self.fraud_result

    @classmethod
    def from_response(cls, json: dict) -> 'IDMResponse':
        """ Parse received response and stores it as a document. """
        response = parse_response(json)
        transaction_id = response['transaction_id']

        if transaction_id[:3] == 'csv':
            user = User.objects(id=transaction_id[3:]).first()
        else:
            related_request = IDMRequest.objects(transaction_id=transaction_id).first()
            user = related_request.user if related_request else None

        obj = cls(
            response_data=json,
            user=user if user else None,
            **response,
        ).save()
        cls.on_received.send(obj)
        return obj

    @property
    def request(self) -> IDMRequest:
        return IDMRequest.objects(transaction_id=self.transaction_id).first()

    @classmethod
    def empty(cls):
        return cls(
            user=None,
            transaction_id=str(ObjectId()),
            result=STATUS_PENDING,
        )
