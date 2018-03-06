from flask import Blueprint, jsonify, request
from voluptuous import All, Length, REMOVE_EXTRA, Range

from errors import ValidationError
from schema import Schema
from upload.models import Upload
from user.auth import authenticate
from user.models import User

blueprint = Blueprint('uploads', __name__)


@blueprint.route('/v1/upload', methods=['POST'])
@authenticate()
def new_upload(user: User):
    schema = Schema({
        'filename': All(Length(3, 250), str),
        'content_type': All(Length(5, 20), str),
        'size': Range(100, 4 * 1024 * 1024),  # 400KB..4MB
    }, extra=REMOVE_EXTRA, required=True)
    data = schema(request.json)

    try:
        ext = data['filename'].split('.')[1].lower()
    except:
        raise ValidationError('Invalid file')

    # if ext not in ['gif', 'jpeg', 'jpg', 'png']:
    #     raise ValidationError('Invalid file')

    upload = Upload.create(
        user=user,
        original_filename=data['filename'],
        content_type=data['content_type'],
        size=data['size'],
    )
    return jsonify({'put_url': upload.put_url, 'id': str(upload.id)})
