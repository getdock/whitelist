import datetime
import os

DEBUG = False

CURRENT_RELEASE = os.environ.get('CURRENT_RELEASE')
CURRENT_ENVIRONMENT = os.environ.get('CURRENT_ENVIRONMENT')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # this fixes the problem
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'NOTSET',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'NOTSET',
            'propagate': True
        }
    }
}

DOCK_PER_ETH = 1 / 0.00009333  # Amount of DOCK tokens one can get for a single ETH


with open('eths.txt', 'r') as fh:
    WHITELISTED_ADDRESSES = {itm.strip() for itm in fh}

ETH_BALANCE_ADDRESS = os.environ.get('ETH_BALANCE_ADDRESS', '')
ETH_ADDRESS = os.environ.get('ETH_ADDRESS')
ETH_MAX_CONTRIBUTION = float(os.environ.get('ETH_MAX_CONTRIBUTION', '0.01'))

ONFIDO_TOKEN = os.environ.get('ONFIDO_TOKEN')
IDM_USERNAME = os.environ.get('IDM_USERNAME')
IDM_PASSWORD = os.environ.get('IDM_PASSWORD')
IDM_URL = 'https://edna.identitymind.com/im/account/consumer'  # PROD
# IDM_URL = 'https://staging.identitymind.com/im/account/consumer'  # STAGING
# IDM_URL = 'https://sandbox.identitymind.com/im/account/consumer'  # SANDBOX
IDM_WEBHOOK_USERNAME = os.environ.get('IDM_WEBHOOK_USERNAME')
IDM_WEBHOOK_PASSWORD = os.environ.get('IDM_WEBHOOK_PASSWORD')

VERIFIED_IDS_CAP = os.environ.get('VERIFIED_IDS_CAP', 25000)  # Don't submit ids to idm after we've reached this cap

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET = os.environ.get('AWS_BUCKET')

CUSTOMER_IO_SITE_ID = os.environ.get('CUSTOMER_IO_SITE_ID')
CUSTOMER_IO_API_KEY = os.environ.get('CUSTOMER_IO_API_KEY')

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_ADMINS = [int(item) for item in os.environ.get('TELEGRAM_ADMINS', '').split(',') if item]
TELEGRAM_ADMIN_CHANNEL = os.environ.get('TELEGRAM_ADMIN_CHANNEL')
TELEGRAM_PUBLIC_CHANNEL = os.environ.get('TELEGRAM_PUBLIC_CHANNEL')

WHITELIST_CLOSED = os.environ.get('WHITELIST_CLOSED', False) in ['yes', 'true', '1', 'y', 't']

# UTC timestamp of when  whitelist should be opened
WHITELIST_OPEN_DATE = os.environ.get('WHITELIST_OPEN_TS', None)
if WHITELIST_OPEN_DATE:
    try:
        WHITELIST_OPEN_DATE = datetime.datetime.utcfromtimestamp(int(WHITELIST_OPEN_DATE))
    except:
        WHITELIST_OPEN_DATE = None

SALT = os.environ.get('SALT', 'salt')
