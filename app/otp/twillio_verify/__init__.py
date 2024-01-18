from django.conf import settings
from twilio.rest import Client


class TwilioBaseHelper:
    _account_sid = settings.TWILIO_ACCOUNT_SID
    _auth_token = settings.TWILIO_AUTH_TOKEN
    _client = None

    def __init__(self):
        self._client = Client(self._account_sid, self._auth_token)

    @property
    def client(self):
        return self._client
