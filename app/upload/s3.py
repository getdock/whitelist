import shutil
from gzip import GzipFile
from io import BytesIO

import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from config import AWS_ACCESS_KEY_ID, AWS_BUCKET, AWS_SECRET_ACCESS_KEY


class S3(object):
    _connection = None

    @property
    def connection(self):
        if not self._connection and not AWS_ACCESS_KEY_ID:
            return

        if not self._connection:
            self._connection = S3Connection(
                AWS_ACCESS_KEY_ID,
                AWS_SECRET_ACCESS_KEY,
                calling_format=boto.s3.connection.OrdinaryCallingFormat()
            )
        return self._connection

    def file_size(self, filename):
        bkt = self.connection.get_bucket(AWS_BUCKET, validate=False)
        key = bkt.lookup(filename)
        if not key:
            raise KeyError(filename)
        return key.size

    def key(self, filename):
        bkt = self.connection.get_bucket(AWS_BUCKET, validate=False)
        key = Key(bkt)
        key.key = filename
        return key

    def put(self, filename, data, content_type=None, **meta):
        if not self.connection:
            return None
        key = self.key(filename)
        if content_type:
            key.content_type = content_type
        for k, v in meta.items():
            key.set_metadata(k, v)
        key.set_contents_from_string(data)
        return key

    def get(self, filename):
        if not self.connection:
            return None
        key = self.key(filename)
        return key.read()

    def delete(self, filename):
        if not self.connection:
            return None

        key = self.key(filename)
        if key.exists():
            key.delete()
            return True
        return False

    def public_url(self, filename, bucket_as_domain=True, protocol='https'):
        if bucket_as_domain:
            return f'{protocol}://{AWS_BUCKET}/{filename}'
        else:
            return self.key(filename).generate_url(expires_in=0, query_auth=False)

    def sign_url(self, filename, method='PUT', expire=600, headers=None):
        if not self.connection:
            return None

        return self.connection.generate_url(
            bucket=AWS_BUCKET,
            expires_in=expire,
            force_http=False,
            headers=headers,
            key=filename,
            method=method,
            query_auth=True,
        )

    def upload(
            self,
            filename,
            fileobj=None,
            gzip=False,  # False or gzip compression level (0..9)
            content_type=None,
            signed_duration=36000,
            signed_method='GET',
    ):
        opened = False
        if not fileobj:
            fileobj = open(filename, 'r')
            opened = True

        try:
            if gzip in [None, False]:
                self.put(
                    filename,
                    fileobj.read(),
                    content_type=content_type,
                    **{'Content-Disposition': 'attachment; filename=' + filename}
                )
            else:
                if gzip is True:
                    gzip = 7
                iofh = BytesIO()
                try:
                    with GzipFile(filename, 'wb', gzip, iofh) as gzfileobj:
                        shutil.copyfileobj(fileobj, gzfileobj)

                    filename = '{}.gz'.format(filename)
                    content_type = 'application/gzip'
                    self.put(
                        filename,
                        iofh.getvalue(),
                        content_type=content_type,
                        **{'Content-Disposition': 'attachment; filename=' + filename}
                    )
                finally:
                    iofh.close()

            if signed_duration and signed_method:
                res = self.sign_url(filename, signed_method, signed_duration)
                return res

            return filename
        finally:
            if opened:
                fileobj.close()


s3 = S3()
