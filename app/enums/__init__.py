from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def choices(cls):
        return [(i.value, i.name) for i in cls]

    @classmethod
    def values(cls):
        return list(i.value for i in cls)

    @classmethod
    def count(cls):
        return len(cls)

    @classmethod
    def mapping(cls):
        return dict((i.name, i.value) for i in cls)


class UserGenderType(BaseEnum):
    MALE = "Male"
    FEMALE = "Female"
    

class UserAccountType(BaseEnum):
    SUPER_ADMINISTRATOR = "SUPER_ADMINISTRATOR"
    ADMINISTRATOR = "ADMINISTRATOR"
    ACCOUNTANT = "ACCOUNTANT"
    ENFORCEMENT_OFFICER = "ENFORCEMENT_OFFICER"
    AGENT = "AGENT"
    INDIVIDUAL = "INDIVIDUAL"
    COOPERATE = "COOPERATE"
    CONSULTANT = "CONSULTANT"
    GOVRNMENT_MDA = "GOVRNMENT_MDA"
    RELATION_OFFICER = "RELATION_OFFICER"
    

class BussinessType(BaseEnum):
    KEKE = "KEKE"
    TAXI = "TAXI"
    BUS = "BUS"
    TRUCK = "TRUCK"


class AdminGroupType(BaseEnum):
    VERIFICATION_OFFICER = "VerificationOfficer"
    REPORT_OFFICER = "ReportOfficer"


class OTPVerificationChannel(BaseEnum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    CALL = "call"


class NotificationCallToActionType(BaseEnum):
    VIEW_USER_PROFILE = "View User Profile"
    CONTACT_ADMIN = "Contact Admin"
    REPORT_USER = "Report User"
    GO_TO_MY_PROFILE_SETTINGS = "Go To My Profile Settings"


class GenericStatus(BaseEnum):
    FULFILLED = "Fulfilled"
    PENDING = "Pending"
    CANCELLED = "Cancelled"


class ElkStatus(BaseEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PENDING = "PENDING"

class PaymentStatus(BaseEnum):
    PAID = "PAID"
    UNPAID = "UNPAID"
    PENDING = "PENDING"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaymentFrequency(BaseEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"

