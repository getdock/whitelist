import os

MONGODB_URI = os.environ.get('MONGODB_URI')
SENTRY_DSN = os.environ.get('SENTRY_DSN')

TESTING = False
DEBUG = False

SALT = os.environ.get('SALT')
