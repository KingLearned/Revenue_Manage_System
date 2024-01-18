import hashlib
from botocore.exceptions import ClientError
import boto3
from django.conf import settings

from . import AWSPinpointBase


class AWSPinpointVerify(AWSPinpointBase):
    __slots__ = ["_phone_number", "_source", "_validity_period"]

    def __init__(self, phone_number):
        self._phone_number = phone_number
        self._source = "VerifyPhoneNumber"
        self._validity_period = settings.OTP_EXPIRATION_MINS
        super().__init__()

    @property
    def ref_id(self):
        refId = self._brand_name + self._source + self._phone_number
        return hashlib.md5(refId.encode()).hexdigest()

    @property
    def client(self):
        return boto3.client(
            "pinpoint",
            region_name=self._application_region,
            aws_access_key_id=self._aws_access_key_id,
            aws_secret_access_key=self._aws_secret_access_key,
        )

    def send_sms(self, receiver, text, channel="sms"):
        try:
            response = self.client.send_messages(
                ApplicationId=self._application_id,
                MessageRequest={
                    "Addresses": {receiver: {"ChannelType": "SMS"}},
                    "MessageConfiguration": {
                        "SMSMessage": {"Body": text, "MessageType": "TRANSACTIONAL"}
                    },
                },
            )

        except ClientError as e:
            print(f"{e.response=}")
            return False, e.response
        else:
            print(f"{response=}")
            return True, response

    def send_otp_verify(self, channel="sms"):
        try:
            response = self.client.send_otp_message(
                ApplicationId=self._application_id,
                SendOTPMessageRequestParameters={
                    "Channel": "SMS",
                    "BrandName": self._brand_name,
                    "CodeLength": 6,
                    "ValidityPeriod": self._validity_period,
                    "AllowedAttempts": self._otp_max_attempts,
                    "Language": "en-US",
                    "OriginationIdentity": self._origination_identity,
                    "DestinationIdentity": self._phone_number,
                    "ReferenceId": self.ref_id,
                },
            )
        except ClientError as e:
            return False, e.response
        else:
            return True, response

    def verify_otp_sent(self, otp: str) -> bool:
        try:
            response = self.client.verify_otp_message(
                ApplicationId=self._application_id,
                VerifyOTPMessageRequestParameters={
                    "DestinationIdentity": self._phone_number,
                    "ReferenceId": self.ref_id,
                    "Otp": otp,
                },
            )

        except ClientError as e:
            return False
        else:
            if response.get("VerificationResponse").get("Valid"):
                return True
            return False
