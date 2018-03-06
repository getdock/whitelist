from bson import ObjectId
from itsdangerous import BadSignature, URLSafeSerializer

from config import SALT


def signer() -> URLSafeSerializer:
    return URLSafeSerializer(SALT, salt=f'whitelist')


def get_token(user_id: ObjectId) -> str:
    return signer().dumps([str(user_id)])


def verify_token(token: str) -> ObjectId:
    try:
        [user_id] = signer().loads(token)
    except BadSignature:
        raise ValueError()

    return ObjectId(user_id)
