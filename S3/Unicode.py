from . import Config

def unicodise(string, encoding = None, errors = "replace"):
    """
    Convert 'string' to Unicode or raise an exception.
    """

    if not encoding:
        encoding = Config.Config().encoding

    if type(string) == six.text_type:
        return string
    debug("Unicodising %r using %s" % (string, encoding))
    try:
        return six.text_type(string, encoding, errors)
    except UnicodeDecodeError:
        raise UnicodeDecodeError("Conversion to unicode failed: %r" % string)

def deunicodise(string, encoding = None, errors = "replace"):
    """
    Convert unicode 'string' to <type str>, by default replacing
    all invalid characters with '?' or raise an exception.
    """

    if not encoding:
        encoding = Config.Config().encoding

    if type(string) != six.text_type:
        return str(string)
    debug("DeUnicodising %r using %s" % (string, encoding))
    try:
        return string.encode(encoding, errors)
    except UnicodeEncodeError:
        raise UnicodeEncodeError("Conversion from unicode failed: %r" % string)

def unicodise_safe(string, encoding = None):
    """
    Convert 'string' to Unicode according to current encoding
    and replace all invalid characters with '?'
    """

    return unicodise(deunicodise(string, encoding), encoding).replace(u'\ufffd', '?')
