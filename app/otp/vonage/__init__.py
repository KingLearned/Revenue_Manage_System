# import vonage
# from django.conf import settings

# from apps.user.helpers.auth import UserAuthHelpers
# from apps.utils.helpers import redis


# class NexmoClient:
#     def __init__(self, phone_number):
#         self._phone_number = phone_number
#         self._brand_name = settings.AWS_PINPOINT_APPLICATION_BRAND_NAME
#         self.client = vonage.Client(
#             key=settings.NEXMO_API_KEY, secret=settings.NEXMO_API_SECRET
#         )
#         self.verify = vonage.Verify(self.client)
#         self.sms = vonage.Sms(self.client)

#     def send_sms(self, receiver, text, channel="sms"):
#         try:
#             response = self.sms.send_message(
#                 {
#                     "from": self._brand_name,
#                     "to": receiver,
#                     "text": text,
#                 }
#             )

#             if response["messages"][0]["status"] == "0":
#                 print("Message sent successfully.")
#             else:
#                 print(
#                     f"Message failed with error: {response['messages'][0]['error-text']}"
#                 )
#         except Exception as err:
#             return False, err
#         else:
#             return True, None

#     def send_otp_verify(self, channel="sms"):
#         cache_instance = redis.RedisTools(
#             UserAuthHelpers.get_phone_number_for_nexmo(self._phone_number),
#             ttl=settings.VERIFICATION_CHANNEL_EXPIRATION_SECS,
#         )
#         try:
#             response = self.verify.start_verification(
#                 number=self._phone_number,
#                 brand=self._brand_name,
#             )

#             print(response)
#             if response["status"] == "0":
#                 print(f"Verification request started for {response['request_id']}")
#                 cache_instance.cache_value = {"request_id": response["request_id"]}

#             else:
#                 print(f"Error: {response['error_text']}")
#         except Exception as err:
#             return False, err
#         else:
#             return True, response

#     def verify_otp_sent(self, otp):
#         cache_instance = redis.RedisTools(
#             UserAuthHelpers.get_phone_number_verification_channel(self._phone_number),
#             ttl=settings.VERIFICATION_CHANNEL_EXPIRATION_SECS,
#         )
#         try:
#             response = self.verify.check(
#                 request_id=cache_instance.cache_value.get("request_id"),
#                 code=otp,
#             )
#         except Exception as err:
#             return False, err
#         else:
#             print(response)
#             if response["status"] == "0":
#                 print("Verification successful!")
#                 return True, response
#             else:
#                 print(f"Error: {response['error_text']}")
#                 return False, None
