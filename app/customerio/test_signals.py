from bson import ObjectId
from mock import patch

from customerio.const import EVENT_TRANSITION
from user.models import User
from user.state import INFO_NOT_VERIFIED, NEW_USER
from user.test_user_info import new_user


def test_identify_new_user(service, customer):
    mocked_id = ObjectId()
    with patch('user.models.ObjectId') as oid:
        oid.return_value = mocked_id
        user = User(id=mocked_id)
        with customer(user) as call:
            res = service.post('/v1/user', new_user())
            assert res.status_code == 201, res.json
            assert call.identified
            assert call.has_event(EVENT_TRANSITION, {'state_before': NEW_USER, 'state_now': INFO_NOT_VERIFIED})
