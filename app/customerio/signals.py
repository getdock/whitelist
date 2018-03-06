import logging

from customerio.client import customerio
from customerio.const import EVENT_TRANSITION
from customerio.geo import name_by_iso
from ids.const import IDS_NAMES
from ids.models import IDUpload
from onfid.const import CHECK_COMPLETE
from onfid.models import Check
from signals import Transition, connect
from user.models import User

log = logging.getLogger(__name__)


@connect(User.on_create)
def identify_user(user: User, **_):
    try:
        customerio.identify(user, ip=user.ip, idm_tid=user.idm_tid)
    except:
        log.exception('Customer error')


@connect(User.on_transition)
def on_transition(user: User, transition: Transition):
    try:
        customerio.event(user, EVENT_TRANSITION, state_before=transition[0], state_now=transition[1])
    except:
        log.exception('Customer transition error')


@connect(IDUpload.on_create)
def id_uploaded(upload: IDUpload, **_):
    try:
        customerio.identify(
            upload.user,
            doc_type=upload.doc_type,
            doct_type_name=IDS_NAMES.get(upload.doc_type),
            doc_county=upload.doc_country,
            doc_country_name=name_by_iso.get(upload.doc_country),
            doc_state=upload.doc_state,
        )
    except:
        log.exception('Customer error')


@connect(User.on_transition)
def update_users_state(user: User, transition: Transition):
    try:
        customerio.identify(user)
    except:
        log.exception('Customer error')


@connect(Check.on_update)
def update_user_status_on_complete_check(check: Check, **_):
    if check.status != CHECK_COMPLETE:
        return

    if not check.user:
        log.exception('Check missing user: %s', check.id)
        return

    customerio.identify(check.user)


@connect(Check.on_update)
def store_check_event(check: Check, **_):
    if not check.user:
        log.exception('Check missing user: %s', check.id)
        return

    user = check.user
    customerio.event(user, 'onfido_check_update', **check.raw)
