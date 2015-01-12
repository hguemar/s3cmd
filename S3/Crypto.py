## Amazon S3 manager
## Author: Michal Ludvig <michal@logix.cz>
##         http://www.logix.cz/michal
## License: GPL Version 2
## Copyright: TGRMN Software and contributors

import sys
import hmac
import base64

import Config
from logging import debug

import os
import datetime
import urllib

#
# the following is necessary because of the incompatibilities
# between Python 2.4, 2.5, and 2.6 as well as the fact that some
# people running 2.4 have installed hashlib as a separate module
# this fix was provided by boto user mccormix.
# see: http://code.google.com/p/boto/issues/detail?id=172
# for more details.
#
try:
    from hashlib import sha1
    from hashlib import sha256
    if sys.version[:3] == "2.4":
        # we are using an hmac that expects .new() and __call__() methods.
        class Faker:
            def __init__(self, which):
                self.which = which
                self.digest_size = self.which().digest_size
            def new(self, *args, **kwargs):
                return self.which(*args, **kwargs)
            def __call__(self, *args, **kwargs):
                return self.which(*args, **kwargs)
                        
        sha1 = Faker(sha1)
        sha256 = Faker(sha256)
except ImportError:
    import sha as sha1
    sha256 = None


__all__ = []

### AWS Version 2 signing
def sign_string_v2(string_to_sign):
    """Sign a string with the secret key, returning base64 encoded results.
    By default the configured secret key is used, but may be overridden as
    an argument.

    Useful for REST authentication. See http://s3.amazonaws.com/doc/s3-developer-guide/RESTAuthentication.html
    """
    signature = base64.encodestring(hmac.new(Config.Config().secret_key, string_to_sign, sha1).digest()).strip()
    return signature
__all__.append("sign_string_v2")

def sign_url_v2(url_to_sign, expiry):
    """Sign a URL in s3://bucket/object form with the given expiry
    time. The object will be accessible via the signed URL until the
    AWS key and secret are revoked or the expiry time is reached, even
    if the object is otherwise private.

    See: http://s3.amazonaws.com/doc/s3-developer-guide/RESTAuthentication.html
    """
    return sign_url_base_v2(
        bucket = url_to_sign.bucket(),
        object = url_to_sign.object(),
        expiry = expiry
    )
__all__.append("sign_url_v2")

def sign_url_base_v2(**parms):
    """Shared implementation of sign_url methods. Takes a hash of 'bucket', 'object' and 'expiry' as args."""
    parms['expiry']=time_to_epoch(parms['expiry'])
    parms['access_key']=Config.Config().access_key
    parms['host_base']=Config.Config().host_base
    debug("Expiry interpreted as epoch time %s", parms['expiry'])
    signtext = 'GET\n\n\n%(expiry)d\n/%(bucket)s/%(object)s' % parms
    debug("Signing plaintext: %r", signtext)
    parms['sig'] = urllib.quote_plus(sign_string_v2(signtext))
    debug("Urlencoded signature: %s", parms['sig'])
    return "http://%(bucket)s.%(host_base)s/%(object)s?AWSAccessKeyId=%(access_key)s&Expires=%(expiry)d&Signature=%(sig)s" % parms

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), sha256).digest()

def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def sign_string_v4(method='GET', host='', canonical_uri='/', params={}, region='us-east-1', cur_headers={}, body=''):
    service = 's3'

    cfg = Config.Config()
    access_key = cfg.access_key
    secret_key = cfg.secret_key

    t = datetime.datetime.utcnow()
    amzdate = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d')

    splits = canonical_uri.split('?')
    canonical_uri = quote_param(splits[0], quote_backslashes=False)
    canonical_querystring = ''
    qs_array = []
    for qs in splits[1:]:
        replacement = '%s='
        if '=' in qs:
            replacement = '%s'
        qs_array.append(replacement % qs)
    canonical_querystring += '&'.join(qs_array)

    if type(body) == type(sha256('')):
        payload_hash = body.hexdigest()
    else:
        payload_hash = sha256(body).hexdigest()

    canonical_headers = 'host:' + host + '\n' + 'x-amz-content-sha256:' + payload_hash + '\n' + 'x-amz-date:' + amzdate + '\n'
    signed_headers = 'host;x-amz-content-sha256;x-amz-date'

    for header in cur_headers.keys():
        # avoid duplicate headers and previous Authorization
        if header == 'Authorization' or header in signed_headers.split(';'):
            continue
        canonical_headers += header.strip() + ':' + str(cur_headers[header]).strip() + '\n'
        signed_headers += ';' + header.strip()

    # sort headers
    canonical_headers = '\n'.join(sorted(canonical_headers.split())) + '\n'
    signed_headers = ';'.join(sorted(signed_headers.split(';')))

    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
    debug('Canonical Request:\n%s\n----------------------' % canonical_request)

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  sha256(canonical_request).hexdigest()
    signing_key = getSignatureKey(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), sha256).hexdigest()
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ',' +  'SignedHeaders=' + signed_headers + ',' + 'Signature=' + signature
    headers = dict(cur_headers.items() + {'x-amz-date':amzdate, 'Authorization':authorization_header, 'x-amz-content-sha256': payload_hash}.items())
    debug("signature-v4 headers: %s" % headers)
    return headers

def quote_param(param, quote_backslashes=True):
    # As stated by Amazon the '/' in the filename should stay unquoted and %20 should be used for space instead of '+'
    quoted = urllib.quote_plus(urllib.unquote_plus(param), safe='~').replace('+', '%20')
    if not quote_backslashes:
        quoted = quoted.replace('%2F', '/')
    return quoted

def checksum_sha256(filename, offset=0, size=None):
    canonical_uri = urllib.quote_plus(filename, safe='~').replace('%2F', '/')
    try:
        hash = sha256()
    except:
        # fallback to Crypto SHA256 module
        hash = sha256.new()
    f = open(filename, 'rb')
    if size is None:
        while True:
            chunk = chunk = f.read(8192)
            if not chunk:
                break
            hash.update(chunk)
    else:
        f.seek(offset)
        chunk = f.read(size)
        hash.update(chunk)
    return hash
