from django.utils import timezone
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from rest_framework_simplejwt.tokens import RefreshToken
from app import enums
from dateutil.relativedelta import relativedelta
from app.base import BaseModelMixin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_celery_beat.models import PeriodicTask
from app.decorators import ModelDecorators
from config.celery.queue import CeleryQueue
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from app import tasks as background_tasks

class User(AbstractUser):
    abssin_num = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=10, null=True, blank=True)
    is_agent = models.BooleanField(default=False)
    is_enforcer = models.BooleanField(default=False)
    marital_status = models.CharField(max_length=10, null=True, blank=True, choices=(
        ('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widowed', 'Widowed')))
    gender = models.CharField(
        _("Gender"),
        choices=enums.UserGenderType.choices(),
        null=True,
        blank=True,
        max_length=50,
    )
    phone_number = models.CharField(max_length=11)
    dob = models.DateField(_("Date of Birth"), null=True, blank=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    state_of_origin = models.CharField(max_length=255, null=True, blank=True)
    lga = models.ForeignKey('LGA', on_delete=models.SET_NULL, null=True, blank=True)
    ward = models.ForeignKey('Ward', on_delete=models.SET_NULL, null=True, blank=True)
    place_of_birth = models.CharField(max_length=255, null=True, blank=True)
    next_of_kin = models.CharField(max_length=255, null=True, blank=True)
    passport = models.ImageField(upload_to='passport', null=True, blank=True)
    # revenue_stream = models.ForeignKey('RevenueStream', on_delete=models.SET_NULL, null=True)
    # collection_area = models.ForeignKey('CollectionArea', on_delete=models.SET_NULL, null=True)
    bvn_number = models.CharField(max_length=11, blank=True, null=True)
    nin_number = models.CharField(max_length=11, null=True, blank=True)
    bussiness_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    owing = models.BooleanField(default=False)
    account_type = models.CharField(
        _("Account Type"),
        choices=enums.UserAccountType.choices(),
        default=enums.UserAccountType.INDIVIDUAL.value,
        null=False,
        blank=False,
        max_length=20,
    )

    @property
    def is_admin(self):
        return (
            self.account_type and self.account_type == enums.UserAccountType.ADMINISTRATOR.value
        )

    @property
    def is_super_admin(self):
        return self.account_type == enums.UserAccountType.SUPER_ADMINISTRATOR.value

    @property
    def full_name(self):
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    @property
    def is_admin_type(self):
        return self.account_type in [
            enums.UserAccountType.ADMINISTRATOR.value,
            enums.UserAccountType.SUPER_ADMINISTRATOR.value,
        ]

    @property
    def age(self):
        return self.dob and relativedelta(timezone.now().date(), self.dob).years

    def send_otp(self, channel="sms"):
        assert (
            self.phone_number
        ), "User must have a valid phone number defined for OTP Verification"
        # background_tasks.send_otp_to_user.apply_async(
        #     (self.id, channel), queue=CeleryQueue.Definitions.ACCOUNT_VERIFICATION
        # )

    @staticmethod
    def send_sms(receiver, text, channel="sms"):
        assert (
            receiver.phone_number
        ), "User must have a valid phone number to receive sms"
        # background_tasks.send_sms_to_user.apply_async(
        #     (receiver.phone_number, text, channel),
        #     queue=CeleryQueue.Definitions.EMAIL_AND_SMS_NOTIFICATION,
        # )

    def retrieve_auth_token(self):
        data = {}
        refresh = RefreshToken.for_user(self)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        return data


    def notify_user(self, subject, message) -> bool:
        try:
            self.send_mail(subject, message)
            return True
        except Exception:
            return False
    
    def __str__(self):
        return self.username


class AgentManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_agent=True)
    
class EnforcerManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_enforcer=True)

    
class LGA(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Ward(models.Model):
    name = models.CharField(max_length=255)
    lga = models.ForeignKey(LGA, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name


class Transports(models.Model):
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    
class Markets(models.Model):
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class InformalSector(models.Model):
    owner = models.CharField(max_length=255)
    owner_phone_number = models.CharField(max_length=11)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    date_paid = models.DateField(blank=True, null=True)
    reference_number = models.CharField(max_length=50, unique=True)
    account_number = models.CharField(max_length=50, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    owing = models.BooleanField(default=False)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, null=True, blank=True)
    
    def get_lga(self):
        if self.ward:
            return self.ward.lga
        return None

    def __str__(self):
        return f"{self.owner} - {self.content_type} - {self.object_id}"



class UserSession(BaseModelMixin):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    refresh = models.CharField(
        max_length=255, unique=True, null=True, blank=True)
    access = models.CharField(
        max_length=255, unique=True, null=True, blank=True)
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"

    def __str__(self):
        return f"{self.user} - {self.last_activity}"


class Payment(BaseModelMixin):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=50, unique=True)
    account_number = models.CharField(max_length=50, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    owing = models.BooleanField(default=False)
    payment_for = models.CharField(max_length=255, null=True, blank=True)
    
    # Polymorphic relationship fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    source = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.source} Payment - {self.date_paid}"


class Agent(User):
    class Meta:
        proxy = True
        verbose_name = "Agent"
        verbose_name_plural = "Agents"

    objects = AgentManager()


class Enforcer(User):
    class Meta:
        proxy = True
        verbose_name = "Enforcer"
        verbose_name_plural = "Enforcers"

    objects = EnforcerManager()
