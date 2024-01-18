from datetime import datetime
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *


class DOBValidator:
    def __call__(self, value):
        current_day = datetime.now().date()
        if value is not None and current_day < value:
            message = f"DOB must be earlier than today"
            raise serializers.ValidationError(message, code="invalid DOB")


class UserSerializer:
    class List(serializers.ModelSerializer):
        class Meta:
            model = get_user_model()
            fields = [
                "id",
                "first_name",
                "last_name",
                "username",
                "email",
                "date_joined",
                "account_type",
                "hide_full_name",
            ]
            ref_name = "User - List"

    
    class Update(serializers.ModelSerializer):
        username = serializers.CharField(
            allow_blank=False,
            allow_null=True,
            max_length=150,
        )
        phone_number = serializers.CharField(required=False)
        
        @staticmethod
        def validate_dob(value):
            DOBValidator()(value)
            return value

        class Meta:
            model = get_user_model()
            fields = '__all__'

            ref_name = "User - Update"


    class Retrieve(serializers.ModelSerializer):
        age = serializers.IntegerField(read_only=True)

        class Meta:
            model = get_user_model()
            exclude = [
                "id",
                "password",
                "is_superuser",
                "is_staff",
                "is_active",
                "groups",
                "user_permissions",
            ]

            ref_name = "User - Retrieve"

class LgaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LGA
        fields = '__all__'


class MarketsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Markets
        fields = '__all__'


class TransportsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transports
        fields = '__all__'


class WardSerializer(serializers.ModelSerializer):
    lga = LgaSerializer()

    class Meta:
        model = Ward
        fields = ('id', 'name', 'lga')

class InformalSectorSerializer(serializers.ModelSerializer):
    ward = WardSerializer()

    class Meta:
        model = InformalSector
        fields = ('id', 'owner', 'owner_phone_number', 'content_type', 'object_id', 'date_paid',
                  'reference_number', 'account_number', 'bank_name', 'balance', 'amount_owed', 'owing', 'ward')

    def get_content_object_serializer(self, obj):
        content_type = obj.content_type
        if content_type.model == 'markets':
            serializer = MarketsSerializer(content_type.get_object_for_this_type(pk=obj.object_id))
        elif content_type.model == 'transports':
            serializer = TransportsSerializer(content_type.get_object_for_this_type(pk=obj.object_id))
        else:
            return None
        return serializer

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lga_info = instance.get_lga()
        if lga_info:
            lga_name = lga_info.name
            if 'ward' in data and 'lga' in data['ward']:
                data['ward']['lga']['name'] = lga_name
        
        content_object_serializer = self.get_content_object_serializer(instance)
        if content_object_serializer:
            content_object_data = content_object_serializer.data
            data['content_object'] = content_object_data
        
        return data

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'


class EnforcerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enforcer
        fields = '__all__'


