import logging

from idm.errors import IDMError
from idm.models import IDMResponse
from idm.const import STATUS_ACCEPTED, STATUS_DECLINED, STATUS_PENDING
from idm.verify import verify
from ids.models import IDUpload
from user.models import User
from user.state import (
    DECLINE_IDM_INFO,
    ID_FAILED,
    ID_PENDING_VERIFICATION,
    ID_VERIFIED,
    INFO_DECLINED,
    INFO_FAILED,
    INFO_PENDING_VERIFICATION,
    INFO_VERIFIED,
)

log = logging.getLogger(__name__)


def verify_info(user: User) -> str:
    state = user.transition(INFO_PENDING_VERIFICATION)

    # Make sure that state didn't changed after we reached pending verification state
    if state != INFO_PENDING_VERIFICATION:
        return state

    try:
        response = verify(user, kyc=True)
        apply_response(user, response, True)
    except IDMError as err:
        return user.transition(INFO_FAILED, details=err.text)


def verify_ids(upload: IDUpload) -> str:
    user = upload.user
    state = user.transition(ID_PENDING_VERIFICATION)

    # Make sure that state didn't changed after we reached pending verification state
    if state != ID_PENDING_VERIFICATION:
        return state

    image1 = upload.upload1.to_base64()
    image2 = upload.upload2.to_base64()

    try:
        response = verify(
            user=user,
            kyc=False,
            image1=image1,
            image2=image2,
            doc_type=upload.doc_type,
            doc_state=upload.doc_state,
            doc_country=upload.doc_country,
        )
        if response.user:
            apply_response(user, response, False)
    except IDMError as err:
        return user.transition(ID_FAILED, details=err.text)


def apply_response(user: User, response: IDMResponse, is_info: bool) -> str:
    if is_info:
        user.update(kyc_result=response.status)
    else:
        user.update(idm_result=response.status)

    if response.status == STATUS_DECLINED:
        if is_info:  # KYC is hard-fail
            return user.transition(
                INFO_DECLINED,
                decline_reason=DECLINE_IDM_INFO,
                details=response.user_reputation,
            )
        else:  # IDs are soft-fail - we do nothing and let admin decide
            return user.state
    elif response.status in [STATUS_ACCEPTED, STATUS_PENDING]:
        return user.transition(INFO_VERIFIED if is_info else ID_VERIFIED)
    else:
        log.warning('Got different response from IDM: %s', response.status)
        return user.state
