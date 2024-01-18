from django.conf import settings


class OTPVerifyHandler:
    __slots__ = ["_phone_number", "_channel"]

    @staticmethod
    def format_phone_number(phone_no: str):
        phone_no = phone_no.strip()
        return phone_no if phone_no.startswith("+") else ("+" + phone_no)

    def __init__(self, phone_number, channel):
        self._phone_number = self.format_phone_number(phone_number)
        self._channel = channel

    @property
    def verify_handler(self):
        print(self._phone_number, self._channel)
        if self._channel == "whatsapp":
            from .twillio_verify.verify import TwilioVerifyHelper

            return TwilioVerifyHelper(self._phone_number)
        else:
            # from .vonage import NexmoClient
            # return NexmoClient(self._phone_number)
            from .aws_pinpoint.verify import AWSPinpointVerify

            return AWSPinpointVerify(self._phone_number)

    def verify_send_otp(self, channel="sms"):
        handler = self.verify_handler
        _, res = handler.send_otp_verify(channel)
        if _:
            return res
        else:
            raise Exception(res)

    def verify_send_sms(self, receiver, text, channel="sms"):
        handler = self.verify_handler
        _, res = handler.send_sms(receiver, text, channel)
        if _:
            return res
        else:
            raise Exception(res)

    def verify_authorize_otp(self, otp):
        handler = self.verify_handler
        _ = handler.verify_otp_sent(otp)

        if not _:
            raise Exception
