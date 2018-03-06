import datetime

from bson import ObjectId

from idm.const import STATUS_MAP
from user.models import User


def parse_response(response: dict):
    return {
        'transaction_id': response['mtid'],
        'result': response.get('res'),  # STATUS_*
        'kyc_state': STATUS_MAP[response['state']],  # KYC_STATUS_*  -> STATUS_*
        'user_reputation': response.get('user'),  # USER_REPUTATION_*
        'fraud_result': response.get('frp'),  # STATUS_*
        'previous_reputation': response.get('upr'),  # USER_REPUTATION_*
    }


def build_request(user: User, **kwargs) -> dict:
    return {
        'dob': user.dob.date().isoformat(),
        'scanData': kwargs.get('image1'),
        'backsideImageData': kwargs.get('image2'),
        'stage': kwargs.get('stage', 1),
        'bfn': user.first_name,
        'bln': user.last_name,
        # 'title': user.name,
        'tid': kwargs.get('transaction_id', str(ObjectId())),
        'man': str(user.id),
        'tea': user.email,
        'ip': kwargs.get('ip', user.ip),
        'dfp': user.dfp,
        'dft': kwargs.get('dft', 'AU'),
        'bsn': user.address,
        'bco': user.country_code,
        'bz': user.zip_code,
        'bc': user.city,
        'bs': user.state_code,
        'tti': int(datetime.datetime.utcnow().strftime('%s')),
        'accountCreationTime': int(user.created_at.strftime('%s')),
        'phn': user.phone,
        'memo1': user.eth_address,
        'memo2': user.eth_amount,
        'docCountry': kwargs.get('doc_country'),
        'docState': kwargs.get('doc_state'),
        'docType': kwargs.get('doc_type'),
    }
