import datetime
import json

from cryptography.fernet import Fernet


def encrypt_string(key: bytes, plaintext: str) -> bytes:
    """
    Encrypt an ASCII string using Fernet.
    See https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet
    """
    return Fernet(key).encrypt(plaintext.encode("ascii"))


def decrypt_string(key: bytes, ciphertext: bytes) -> str:
    """
    Decode an ASCII string using Fernet.
    See https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet
    """
    return Fernet(key).decrypt(ciphertext).decode("ascii")


def a_href(url):
    """
    Render a URL as an <a> tag with the URL as both target and text.

        >>> a_href("https://example.net")
        '<a href="https://example.net">https://example.net</a>'

    This is a utility function for Flask templates.

    """
    return f'<a href="{url}">{url}</a>'


def size_at(sizes, *, desired_size):
    """
    Given a list of sizes of Flickr photo, return the info about
    the desired size.
    """
    sizes_by_label = {s["label"]: s for s in sizes}

    # If we have that exact size available, return that!
    if desired_size in sizes_by_label:
        return sizes_by_label[desired_size]

    # Flickr has a published list of possible sizes here:
    # https://www.flickr.com/services/api/misc.urls.html
    #
    # If the desired size isn't available, we can look for alternatives,
    # but this fallback code is deliberately conservative and simple.
    # We're trying to build something that works for Flickypedia,
    # not any combination of Flickr sizes/desired size.
    if desired_size == "Medium" and "Small" in sizes_by_label:
        return sizes_by_label["Small"]

    raise ValueError(f"This photo is not available at size {desired_size!r}")


class DatetimeEncoder(json.JSONEncoder):
    """
    A custom JSON encoder that supports datetimes.

        >>> t = datetime.datetime(2001, 2, 3, 4, 5, 6)
        >>> json.dumps({"t": t}, cls=DatetimeEncoder)
        '{"t": {"type": "datetime.datetime", "value": "2001-02-03T04:05:06"}}'

    This is meant to be used with ``DatetimeDecoder`` -- together, they
    allow you to serialise a datetime value via JSON and preserve its type.

    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return {"type": "datetime.datetime", "value": obj.isoformat()}
        else:  # pragma: no cover
            return obj


class DatetimeDecoder(json.JSONDecoder):
    """
    A custom JSON decoder that supports the datetimes encoded
    by DatetimeEncoder.

        >>> json.loads(
        ...     '{"t": {"type": "datetime.datetime", "value": "2001-02-03T04:05:06"}}',
        ...     cls=DatetimeDecoder)
        {'t': datetime.datetime(2001, 2, 3, 4, 5, 6)}

    """

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.dict_to_object, *args, **kwargs)

    def dict_to_object(self, d):
        if d.get("type") == "datetime.datetime":
            return datetime.datetime.fromisoformat(d["value"])
        else:
            return d
