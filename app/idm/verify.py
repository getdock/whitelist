from config import VERIFIED_IDS_CAP
from idm.const import STATUS_ACCEPTED
from idm.models import IDMRequest, IDMResponse
from user.models import User
from user.state import BANNED_COUNTRIES, ID_VERIFIED


def verify(user: User, kyc: bool = True, **kwargs) -> IDMResponse:
    req = IDMRequest.create(
        user=user,
        stage=1 if kyc else 2,
        image1=kwargs.get('image1'),
        image2=kwargs.get('image2'),
        doc_country=kwargs.get('doc_country'),
        doc_state=kwargs.get('doc_state'),
        doc_type=kwargs.get('doc_type'),
    )

    should_request = user.country_code and user.country_code not in BANNED_COUNTRIES

    if not kyc: # Only pass ids to idm if user successfully passed KYC
        should_request = should_request and user.kyc_result == STATUS_ACCEPTED

    # Hard cap on number of verified ids
    should_request = should_request and User.objects(state=ID_VERIFIED).count() < VERIFIED_IDS_CAP

    if should_request:
        return req.request()

    return IDMResponse.empty()
