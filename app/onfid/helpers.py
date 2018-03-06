import logging
import mimetypes
import os.path
import time
from typing import Callable, Optional

import requests
from onfido import DocumentType

from config import ONFIDO_TOKEN
from ids.const import DRIVING_LICENCE, ID_CARD, PASSPORT, RESIDENCE_PERMIT, UTILITY_BILL
from onfid.api import api
from onfid.geo import iso2_iso3
from upload.models import Upload
from user.models import User

mimetypes.init()
log = logging.getLogger(__name__)

DOC_TYPES = {
    DRIVING_LICENCE: DocumentType.DrivingLicense,
    PASSPORT: DocumentType.Passport,
    ID_CARD: DocumentType.NationalIdentityCard,
    RESIDENCE_PERMIT: DocumentType.WorkPermit,
    UTILITY_BILL: DocumentType.Unknown,  # We don't have that any way
}


def rate_limit(max_per_minute: int) -> Callable:
    interval = 60.0 / float(max_per_minute)

    def decorate(func):
        last_time_called = [0.0]

        def limited_function(*args, **kargs):
            elapsed = time.clock() - last_time_called[0]
            left_to_wait = interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            ret = func(*args, **kargs)
            last_time_called[0] = time.clock()

            return ret

        return limited_function

    return decorate


def create_user(user: User) -> Optional[dict]:
    try:
        # log.debug('Creating user %s', user.id)
        created = api.Applicants.create({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'dob': user.dob.date().isoformat(),
            'telephone': user.phone,  # 'mobile' ?
            'country': iso2_iso3.get(user.country_code, user.country_code),
            'addresses': [
                {
                    'street': user.address[:32],
                    'town': user.city,
                    'state': user.state_code,
                    'postcode': user.zip_code,
                    'country': iso2_iso3.get(user.country_code, user.country_code),
                },
            ],
        })
        # log.info('Created user: %s', created)
        log.info('Onfid id for user %s is %s', user.id, created.get('id', created))
        user.modify(onfid_id=created.get('id'))
        return created
    except Exception as ex:
        log.exception('Onfido create user error: %s', ex)
        return None


def custom_upload(applicant_id: str, document, document_filename: str, doc_type: str, face: bool) -> dict:
    filename, extension = os.path.splitext(document_filename)

    return api.Documents.post(
        "applicants/{0}/documents/".format(applicant_id),
        {"type": doc_type, 'side': 'front' if face else 'back'},
        {"file": (document_filename, document, mimetypes.types_map[extension])}
    )


def upload_file(upload: Upload, doc_type: str, face: bool) -> dict:
    # log.debug('Uploading file %s/%s', doc_type, upload.id)
    res = custom_upload(
        str(upload.user.onfid_id),
        upload.fh,
        f'{upload.id}.{upload.extension}'.lower(),
        DOC_TYPES[doc_type],
        face,

    )
    log.info('Created document: %s/%s as %s', doc_type, upload.id, res.get('id', res))
    return res


def register_webhook(env: str, base_url: str = None) -> dict:
    assert env in ['live', 'sandbox'], 'Env can be "live" or "sandbox"'

    res = requests.post(
        'https://api.onfido.com/v2/webhooks',
        headers={'Authorization': f'Token token={ONFIDO_TOKEN}'},
        json={
            'url': base_url or f'https://whitelist.dock.io/api/v1/onfido/{ONFIDO_TOKEN}',
            'enabled': True,
            'environments': [env],

        }
    )
    return res.json()
