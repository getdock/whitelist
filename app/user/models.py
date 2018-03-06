import datetime

from blinker import Signal
from bson import ObjectId
from mongoengine import BooleanField, DateTimeField, Document, EmailField, FloatField, IntField, StringField, ListField

from tokens import get_token
from user.errors import UserNotFound
from user.state import ALL_DECLINE_REASONS, ALL_STATES, NEW_USER


class User(Document):
    """
    User object in whitelist service.

    """
    meta = {
        'indexes': ['state', 'kyc_result', 'idm_result', 'country_code', 'onfid_id', 'onfid_status'],
    }

    CSV_FIELDS = [
        'id',
        'email',
        'first_name',
        'last_name',
        'state',
        'created_at',
        'eth_address',
        'eth_amount',
        'phone',
        'dob',
        'telegram',
        'doc_type',
        # 'confirmed_location',
        'address',
        'city',
        'state_code',
        'zip_code',
        'country_code',
        'ip_country',
        'contribution_amount',
        'ip',
        'kyc_result',
        'idm_result',
        'decline_reason',
        'onfid_status',
        'info',
        'action',
        'eth_cap',
    ]
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    state = StringField(choices=ALL_STATES, default=NEW_USER)
    decline_reason = StringField(choices=ALL_DECLINE_REASONS)
    info = StringField()

    ip_country = StringField()
    dob = DateTimeField()
    email = EmailField(unique=True, required=True)
    eth_address = StringField(unique=True, sparse=True)
    eth_amount = FloatField()
    eth_cap = FloatField()
    first_name = StringField()
    last_name = StringField()
    phone = StringField()
    ip = StringField()
    dfp = StringField()
    telegram = StringField(unique=True)
    confirmed_location = BooleanField()
    idm_tid = IntField()

    onfid_id = StringField()
    onfid_status = StringField()

    address = StringField()
    city = StringField()
    state_code = StringField()
    zip_code = StringField()
    country_code = StringField()

    kyc_result = StringField()
    idm_result = StringField()
    doc_type = StringField()

    contribution_amount = FloatField(default=0)
    contribution_tx = ListField(StringField())

    medium = StringField()
    reddit = StringField()
    twitter = StringField()
    linkedin = StringField()
    facebook = StringField()

    on_create = Signal()
    on_transition = Signal()

    @classmethod
    def find(cls, uid: ObjectId) -> 'User':
        """ Helper to find user in DB or raise an error. """
        user = cls.objects(id=uid).first()
        if not user:
            raise UserNotFound()

        return user

    @classmethod
    def create(cls, **data) -> 'User':
        obj = cls(id=ObjectId(), **data).save(force_insert=True)
        cls.on_create.send(obj)
        return obj

    def to_json(self):
        return {
            'address': self.address,
            'city': self.city,
            'state_code': self.state_code,
            'zip_code': self.zip_code,
            'country_code': self.country_code,
            'dob': int(self.dob.strftime('%s')) if self.dob else None,
            'email': self.email,
            # 'telegram': self.telegram,
            'confirmed_location': self.confirmed_location,
            'eth_address': self.eth_address,
            'eth_amount': self.eth_amount,
            'state': self.state,
            'eth_cap': self.eth_cap,
            'decline_reason': self.decline_reason,
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'token': get_token(self.id),
        }

    def to_csv(self) -> dict:
        res = {}
        for field in self.CSV_FIELDS:
            if field == 'action':
                value = ''
            elif field == 'email':
                name, domain = self.email.split('@')
                value = f'{name[0]}...{name[-1]}@{domain}'
            elif field == 'id':
                value = str(self.id)
            elif field in ['created_at', 'dob']:
                value = self[field].isoformat()
            elif field == 'telegram':
                value = f'{self.telegram[0]}...{self.telegram[-1]}' if self.telegram else None
            else:
                value = self[field]
            res.update({field: value})
        return res

    def transition(self, new_state: str, decline_reason: str = None, details: str = None) -> str:
        """
        Transition user to new state.

        This will trigger signal to perform operations required for new state.

        :return: Updated state after all signals

        """
        previous = self.state
        self.state = new_state
        if decline_reason:
            self.decline_reason = decline_reason

        if details:
            self.info = details

        self.save()
        self.on_transition.send(self, transition=(previous, self.state))

        # Our state can be changed after signals are completed
        self.reload()
        return self.state

    def __str__(self):
        return f'<User:{self.id}:{self.state}>'
