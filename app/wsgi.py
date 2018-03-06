from gevent import monkey
monkey.patch_all()

import logging
import os

from app import create_app

log = logging.getLogger(__name__)

app = create_app(os.environ.get('CONFIG', 'prod'))

if __name__ == '__main__':
    log.info('Serving requests')
    app.run(host='0.0.0.0', port=8080)
