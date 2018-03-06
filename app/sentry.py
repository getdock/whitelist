import logging

from flask import Flask
from raven import Client, base
from raven.conf import setup_logging as setup_sentry_logging
from raven.contrib.flask import Sentry
from raven.handlers.logging import SentryHandler
from raven.transport.gevent import GeventedHTTPTransport


class DummyClient(base.DummyClient):
    last_event_id = 'dummy'


def setup_sentry(app: Flask):
    sentry_dsn = app.config.get('SENTRY_DSN')
    if not sentry_dsn:
        client = DummyClient()
    else:
        client = Client(
            sentry_dsn,
            transport=GeventedHTTPTransport,
            release=app.config.get('CURRENT_RELEASE'),
            environment=app.config.get('CURRENT_ENVIRONMENT'),
        )

    sentry = Sentry(client=client, logging=True, level=logging.WARNING)
    handler = SentryHandler(client, level=logging.WARNING)
    setup_sentry_logging(handler)
    sentry.init_app(app)

    return sentry, client
