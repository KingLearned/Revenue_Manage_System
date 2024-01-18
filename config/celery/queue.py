from kombu import Queue


class CeleryQueue:
    class Definitions:
        EMAIL_AND_SMS_NOTIFICATION = "email-sms-notification"
        BASE_USER_VERIFICATION = "base-user-verification"
        LOGGING = "logging"
        MISC = "misc"
        CHAT_MESSAGING = "chat-messaging"
        ACCOUNT_VERIFICATION = "account-verification"
        BEATS = "beats"

    @staticmethod
    def queues():
        return tuple(
            (Queue(getattr(CeleryQueue.Definitions, item)))
            for item in filter(
                lambda ref: not ref.startswith("_"), dir(CeleryQueue.Definitions)
            )
        )
