from bson import ObjectId
from flask import Blueprint, jsonify, request
from voluptuous import All, Any, Coerce, In, Length, Optional, REMOVE_EXTRA

from errors import ValidationError
from ids.const import DOC_TYPES
from ids.models import IDUpload
from schema import Schema
from upload.errors import MissingFile
from upload.models import Upload
from user.auth import authenticate
from user.errors import InvalidState
from user.models import User
from user.state import ID_NOT_VERIFIED, INFO_VERIFIED
from user.verifications import verify_ids

blueprint = Blueprint('ids', __name__)


@blueprint.route('/v1/ids', methods=['POST'])
@authenticate()
def submit_ids(user: User):
    """
    Route to create ids upload package.

    User must be in `INFO_VERIFIED` state.
    Will transition user to `ID_NOT_VERIFIED`

    One should call `/v1/ids/<id>/verify` in order to actually start verification process (see docs there)
    """
    if user.state != INFO_VERIFIED:
        raise InvalidState(user.state)

    schema = Schema({
        'upload1': Coerce(ObjectId),
        'upload2': Coerce(ObjectId),
        'doc_type': In(DOC_TYPES),
        'doc_country': All(Length(2, 2), str),
        Optional('doc_state', default=None): Any(None, All(Length(2, 20), str)),
    }, extra=REMOVE_EXTRA, required=True)
    data = schema(request.json)
    upload1 = Upload.objects(user=user, id=data['upload1']).get()
    upload2 = Upload.objects(user=user, id=data['upload2']).get()

    try:
        if not (upload1.stored_size <= 4 * 1024 * 1024):
            raise ValidationError('Invalid image size')

        if not (upload2.stored_size <= 4 * 1024 * 1024):
            raise ValidationError('Invalid image size')
    except KeyError as err:
        raise MissingFile(str(err))

    id_upload = IDUpload.create(
        user=user,
        upload1=upload1,
        upload2=upload2,
        doc_country=data['doc_country'],
        doc_state=data['doc_state'],
        doc_type=data['doc_type'],
    )

    user.update(doc_type=data['doc_type'])
    user.transition(ID_NOT_VERIFIED)

    return jsonify(id_upload.to_json()), 201


@blueprint.route('/v1/ids/<id>/verify', methods=['POST'])
@authenticate()
def verify_ids_package(id: str, user: User):
    """
    Route that does id package verification. This can be a lengthy call, so it's moved into a separate one.

    Expects user to be in `ID_NOT_VERIFIED` state.
    Will transition user to `ID_VERIFIED` on success.

    Returns result of verification in `status` key
    """
    if user.state != ID_NOT_VERIFIED:
        raise InvalidState(user.state)

    try:
        upload_id = ObjectId(id)
    except ValueError:
        raise ValidationError()

    upload = IDUpload.objects(user=user, id=upload_id).get()

    verify_ids(upload)

    return jsonify(user.reload().to_json())
