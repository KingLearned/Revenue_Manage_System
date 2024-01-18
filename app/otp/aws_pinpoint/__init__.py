from django.conf import settings


class AWSPinpointBase:
    __slots__ = [
        "_application_id",
        "_brand_name",
        "_origination_identity",
        "_application_region",
        "_otp_max_attempts",
        "_aws_access_key_id",
        "_aws_secret_access_key",
    ]

    def __init__(self):
        self._application_id = settings.AWS_PINPOINT_APPLICATION_ID
        self._brand_name = settings.AWS_PINPOINT_APPLICATION_BRAND_NAME
        self._origination_identity = (
            settings.AWS_PINPOINT_APPLICATION_ORIGINATION_IDENTITY
        )
        self._application_region = settings.AWS_PINPOINT_APPLICATION_REGION
        self._otp_max_attempts = settings.AWS_PINPOINT_APPLICATION_OTP_MAX_ATTEMPTS
        self._aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self._aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
