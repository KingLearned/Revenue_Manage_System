from django.conf import settings

from . import TwilioBaseHelper


class TwilioVerifyHelper(TwilioBaseHelper):
    _verify_sid = settings.TWILIO_VERIFY_SID
    _phone_number: str

    def __init__(self, phone_number):
        self._phone_number = phone_number
        super().__init__()

    def send_otp_verify(self, channel="sms"):
        verification = self.client.verify.v2.services(
            self._verify_sid
        ).verifications.create(to=self._phone_number, channel=channel)
        return True, verification

    def verify_otp_sent(self, otp: str) -> bool:
        print(otp, self._phone_number)
        verification_check = self.client.verify.v2.services(
            self._verify_sid
        ).verification_checks.create(to=self._phone_number, code=otp)
        return verification_check.status == "approved"


class TwilioSendSmsHelper(TwilioBaseHelper):
    def send_sms_to_user(self, body, from_, to):
        return self.client.messages.create(body=body, from_=from_, to=to)
