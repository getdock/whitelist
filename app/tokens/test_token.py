from bson import ObjectId

from tokens import signer, verify_token

ID = ObjectId('5a6dee770ee97c0001534b3e')
WRITE_TOKEN = 'WyI1YTZkZWU3NzBlZTk3YzAwMDE1MzRiM2UiXQ.dWfypJfoIo6CD5aOSfrkgUVkKSs'


def test_read_signer():
    assert signer().dumps([str(ID)]) == WRITE_TOKEN
    assert signer().loads(WRITE_TOKEN) == [str(ID)]


def test_validate_signer():
    assert verify_token(WRITE_TOKEN) == ID
