"""
Module provides communication with Customer.io api.

http://customer.io/docs/api/rest.html

Using some code from official Python implementation:
https://github.com/customerio/customerio-python
"""

import json
import logging
from typing import Optional, Union

from bson import ObjectId
from requests import HTTPError, Response

from config import CUSTOMER_IO_API_KEY, CUSTOMER_IO_SITE_ID
from session import build_session
from tokens import get_token
from user.models import User

UserOrId = Union[User, ObjectId, str]

log = logging.getLogger('customerio')


class CustomerIO(object):
    """ Customer.io api """

    URL_PREFIX = 'https://track.customer.io/api/v1/customers'
    json_encoder = json.JSONEncoder
    _session = None

    @property
    def session(self):
        if not self._session and not CUSTOMER_IO_API_KEY:
            return

        if not self._session:
            ses = build_session(1000)
            ses.auth = (CUSTOMER_IO_SITE_ID, CUSTOMER_IO_API_KEY)
            ses.headers.update({'Content-Type': 'application/json'})
            self._session = ses
        return self._session

    def request(self, method: str, user_or_id: UserOrId, section: str = None, **body) -> Optional[Response]:
        """ Make request to Customer.io API. """
        if not self.session:
            return

        customer_id = str(getattr(user_or_id, 'id', user_or_id))
        url_bits = [self.URL_PREFIX, customer_id]
        if section:
            url_bits.append(section)
        url = '/'.join(url_bits)
        try:
            req = self.session.request(method, url, json=body)
            req.raise_for_status()
            return req
        except HTTPError as err:
            log.exception('%s - %s', err, err.response.content)
            return err.response

    # === User ===

    def identify(self, user: UserOrId, **kwargs):
        """ Identify a single customer by their unique id, and optionally add attributes. """
        data = user.to_csv()
        data.update(
            email=user.email,
            telegram=user.telegram,
            created_at=int(user.created_at.strftime('%s')),
            dob=int(user.dob.strftime('%s')) if user.dob else None,
            token=get_token(user.id),
        )
        data.update(kwargs)
        return self.request('PUT', user, **data)

    def delete(self, user: UserOrId):
        """ Delete a customer profile. """
        return self.request('DELETE', user)

    # === Event ==

    def event(self, user: UserOrId, event_name: str, **data):
        """ Track an event for a given customer_id """
        return self.request('POST', user, 'events', name=event_name, data=data)


customerio = CustomerIO()
