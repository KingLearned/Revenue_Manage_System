from rest_framework import generics
from app import enums, redis
from app.base import Token
from app.custom_exception import CustomException
import logging
import orjson
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core import validators as django_core_validators
from django.db import transaction
from django.http import QueryDict
from rest_framework import decorators, response, status, viewsets
from rest_framework_simplejwt.tokens import RefreshToken
from app.custom_utils import Utils
from app.models import *
from config.celery.queue import CeleryQueue
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.http import QueryDict
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from app import serializers
from app import mixins as global_mixins
from app import tasks as background_tasks
from rest_framework.response import Response
from app.permissions import *
import requests
from rest_framework.views import APIView
from config import settings
import json
import hashlib
from rest_framework.permissions import AllowAny




UserModel = get_user_model()
logger = logging.getLogger("python-logstash-logger")


class MonnifyCreateReservedAccount(APIView):
    def post(self, request, *args, **kwargs):
        url = "https://sandbox.monnify.com/api/v2/bank-transfer/reserved-accounts"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.MONIFY_API_TOKEN}"
        }

        data = {
            "accountReference": "abc123",
            "accountName": request.data.get["OwnerName"],
            "currencyCode": "NGN",
            "contractCode": "1108004340",
            "customerEmail": "test@tester.com",
            "bvn": "21212121212",
            "customerName": "John Doe", 
            "getAllAvailableBanks": False,
            "preferredBanks": ["035"]
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return Response({"message": "Reserved account created successfully"})
        else:
            return Response({"error": "Failed to create reserved account"}, status=response.status_code)


class AdminLoginViewSet(TokenObtainPairView):

    @staticmethod
    def check_login_status(view_func):
        def wrapper_func(self, request, *args, **kwargs):
            session = UserSession.objects.filter(
                user__username=request.data["login"]
            ).first()
            if session and session.is_active:
                try:
                    token = RefreshToken(session.refresh)
                    token.blacklist()
                except Exception as e:
                    raise CustomException(message="unable to blacklist token")
                session.is_active = False
                session.save()
            return view_func(self, request, *args, **kwargs)

        return wrapper_func

    def post(self, request, *args, **kwargs):
        if not request.data.get("username"):
            return Response(
                data={"message": "Username is required", "status": status.HTTP_400_BAD_REQUEST},
            )

        username = request.data["username"]
        user = User.objects.filter(username=username).first()

        if not user:
            return Response(
                data={"message": "User not found", "status": status.HTTP_404_NOT_FOUND},
            )

        if not user.is_staff:
            return Response(
                data={"message": "Access denied. User is not an admin.", "status": status.HTTP_403_FORBIDDEN}
            )

        if isinstance(request.data, QueryDict):
            request.data._mutable = True
        request.data[UserModel.USERNAME_FIELD] = username
        response = super().post(request, *args, **kwargs)

        session = UserSession.objects.filter(user=user).first()
        if session:
            session.is_active = True
            session.refresh = response.data["refresh"]
            session.access = response.data["access"]
            session.ip_address = request.META.get("REMOTE_ADDR")
            session.user_agent = request.META.get("HTTP_USER_AGENT")
            session.save()
        else:
            UserSession.objects.create(
                user=user,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
                is_active=True,
                refresh=response.data["refresh"],
                access=response.data["access"],
            )

        return response



class AuthLoginView(TokenObtainPairView):

    @staticmethod
    def check_login_status(view_func):
        def wrapper_func(self, request, *args, **kwargs):
            session = UserSession.objects.filter(
                user__username=request.data["login"]
            ).first()
            if session and session.is_active:
                try:
                    token = RefreshToken(session.refresh)
                    token.blacklist()
                except Exception as e:
                    raise CustomException(message="unable to blacklist token")
                session.is_active = False
                session.save()
            return view_func(self, request, *args, **kwargs)

        return wrapper_func
  
    def post(self, request, *args, **kwargs):
        if not request.data.get("username"):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Username or ABSSIN Number is required"},
            )
            
        if isinstance(request.data, QueryDict):
            request.data._mutable = True
        request.data[UserModel.USERNAME_FIELD] = request.data["username"]
        response = super().post(request, *args, **kwargs)

        user = UserModel.objects.get(username=request.data["username"])
        session = UserSession.objects.filter(user=user).first()
        if session:
            session.is_active = True
            session.refresh = response.data["refresh"]
            session.access = response.data["access"]
            session.ip_address = request.META.get("REMOTE_ADDR")
            session.user_agent = request.META.get("HTTP_USER_AGENT")
            session.save()
        else:
            UserSession.objects.create(
                user=user,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
                is_active=True,
                refresh=response.data["refresh"],
                access=response.data["access"],
            )

        return response



class RegisterUserView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer

    @decorators.action(
        detail=False,
        methods=["post"],
    )
    def create(self, request, *args, **kwargs):
        request_data = request.data.copy()
        request_data["account_type"] = enums.UserAccountType.INDIVIDUAL.value

        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        instance.set_password(request_data.get("password"))
        instance.save()
        
        auth_token = instance.retrieve_auth_token()
        serialized_user = serializers.UserSerializer(instance)
        
        response_data = {
            **serialized_user.data,
            "token": auth_token
        }
        
        return Response(
            status=status.HTTP_201_CREATED,
            data=response_data
        )


class TransportsViewSet(generics.ListCreateAPIView):
    authentication_classes = []
    permission_classes = [AdminPermission]
    queryset = Transports.objects.all()
    serializer_class = serializers.TransportsSerializer


class MarketsViewSet(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AdminPermission]
    queryset = Markets.objects.all()
    serializer_class = serializers.MarketsSerializer


class WardsViewSet(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AdminPermission]
    queryset = Ward.objects.all()
    serializer_class = serializers.WardSerializer


class LgaViewSet(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AdminPermission]
    queryset = LGA.objects.all()
    serializer_class = serializers.LgaSerializer


class InformalSectorViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = serializers.InformalSectorSerializer

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                sector_type = request.data.get("sector_type")
                content_object_id = request.data.get("content_object")
                ward_id = request.data.get("ward")
                if sector_type == "markets":
                    content_object = Markets.objects.get(id=content_object_id)
                else:
                    content_object = Transports.objects.get(id=content_object_id)
                ward = Ward.objects.get(id=ward_id)
                informal_sector = InformalSector.objects.create(
                    owner=request.data.get("owner"),
                    owner_phone_number=request.data.get("owner_phone_number"),
                    content_object=content_object,
                    ward=ward,
                    reference_number=request.data.get("reference_number"),
                )
                self.generate_account(informal_sector)
                serialized_informal_sector = serializers.InformalSectorSerializer(informal_sector)
                return Response(
                    data={"message": "Bussiness created successfully", "status": status.HTTP_201_CREATED},
                )

        except Exception as e:
            return Response(
                data={"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
            )

    def list(self, request, *args, **kwargs):
        try:
            queryset = InformalSector.objects.all()
            serializer = serializers.InformalSectorSerializer(queryset, many=True)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                data={"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
            )


    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            queryset = InformalSector.objects.get(id=pk)
            serializer = serializers.InformalSectorSerializer(queryset)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                data={"message": "Bussiness does not exist", "status": status.HTTP_404_NOT_FOUND}
            )
        
    
    def update(self, request, pk=None, *args, **kwargs):
        try:
            queryset = InformalSector.objects.get(id=pk)
            serializer = serializers.InformalSectorSerializer(queryset, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                )
            return Response(
                data={"message": "Invalid data", "status": status.HTTP_400_BAD_REQUEST}
            )
        except Exception as e:
            return Response(
                data={"message": "Error updating bussness", "status": status.HTTP_400_BAD_REQUEST}
            )


    def generate_account(self, instance):
        url = "https://sandbox.monnify.com/api/v2/bank-transfer/reserved-accounts"
        instance = InformalSector.objects.get(id=instance.id)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.MONIFY_API_TOKEN}"
        }

        data = {
            "accountReference": instance.reference_number,
            "accountName": instance.owner,
            "currencyCode": "NGN",
            "contractCode": "1108004340",
            "customerEmail": "mail@payabia.com",
            "customerName": instance.owner, 
            "getAllAvailableBanks": False,
            "preferredBanks": ["035"]
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            try:
                response_json = response.json()
                accounts = response_json.get("responseBody", {}).get("accounts", [])
                if accounts:
                    account_info = accounts[0]
                    account_number = account_info["accountNumber"]
                    bank_name = account_info["bankName"]
                    if account_number and bank_name:
                        instance.account_number = account_number
                        instance.bank_name = bank_name
                        instance.save()
                        print("Reserved account created successfully")
                    else:
                        print("Incomplete account or bank information in the response")
                        print(response_json)
                else:
                    print("No accounts found in the response")
                    print(response_json)
            except KeyError as e:
                print(f"Failed to get required information from response: {e}")
                print(response_json)
            except IndexError as e:
                print(f"Index error occurred: {e}")
                print(response_json)
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                print(response_json)
        else:
            print("Failed to create reserved account")
            print(response.status_code)
            print(response.content)


def validate_payment(request):
        client_secret_key = settings.MONIFY_SECRET_KEY
        
        instance_account = request.json()["responseBody"]["account_number"]
        informal_sector = InformalSector.objects.get(account_number=instance_account)
        
        # Get the received signature from Monnify
        received_signature = request.headers.get('monnify-signature')
        
        
        request_body = json.loads(request.body.decode('utf-8'))

        # Convert request body to a string
        request_body_str = json.dumps(request_body, separators=(',', ':'), sort_keys=True)

        # Calculate hash value
        hashed_value = hashlib.sha512((client_secret_key + request_body_str).encode()).hexdigest()

        if received_signature == hashed_value:
            informal_sector.balance =+ float(request_body["amountPaid"])
            return Response({'message': 'Payment validated successfully.'}, status=200)
        else:
            return Response({'error': 'Invalid payment signature.'}, status=400)






class AuthViewSet(
    global_mixins.CustomRequestDataValidationMixin,
    global_mixins.CountListResponseMixin,
    viewsets.ViewSet,
):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        return self.queryset.all()

    
    def get_required_fields(self):
        if self.action == "create_admin_user":
            return ["token", "email", "password"]
        elif self.action == "set_password":
            return ["password"]
        elif self.action == "change_password":
            return ["old_password", "new_password"]
        elif self.action == "hide_full_name":
            return []
        return []

    def get_permissions(self):
        if self.action in [
            "create_admin_user",
        ]:
            return [IsGuestUser()]
        elif self.action in ["create_admin_invitation"]:
            return super().get_permissions() + [IsAccountType.AdminUser()]
        return super().get_permissions()

    @staticmethod
    def manipulate_request_data_for_email_phone_number_changes(request):
        instance = request.user
        data = request.data

        if isinstance(request.data, QueryDict):
            request.data._mutable = True

        if data.get("email") and data.get("email") != instance.email:
            request.data["is_email_verified"] = False
        if (
            data.get("phone_number")
            and data.get("phone_number") != instance.phone_number
        ):
            request.data["is_phone_number_verified"] = False

    
    @staticmethod
    def generate_username(request):
        instance = request.user
        if isinstance(request.data, QueryDict):
            request.data._mutable = True
        request.data["username"] = instance.generate_username

    @staticmethod
    def validate_phone_number_verification_channel_choice(view_func):
        def func_to_execute(self, request, *args, **kwargs):
            ver_channel = request.data.get("verification_channel")
            if ver_channel not in enums.OTPVerificationChannel.values():
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        "errors": ["invalid verification channel"],
                        "message": f"You specified an invalid verification channel, must of of '{enums.OTPVerificationChannel.values()}'",
                    },
                )
            return view_func(self, request, *args, **kwargs)

        func_to_execute.__name__ = view_func.__name__
        return func_to_execute

    @decorators.action(
        detail=False,
        methods=["get", "patch", "delete"],
        name="me",
        url_path="me",
    )
    def me(self, request, *args, **kwargs):
        if request.method == "GET":
            serializer = self.serializer_class.Retrieve(instance=request.user)
            return response.Response(status=status.HTTP_200_OK, data=serializer.data)
        elif request.method == "PATCH":
            unique_fields = ["phone_number", "email", "username"]
            base_queryset = self.queryset.exclude(id=request.user.id)
            for field in unique_fields:
                if request.data.get(field):
                    value = request.data.get(field)
                    if field == "phone_number":
                        queryset = base_queryset.filter(phone_number=value)
                    elif field == "email":
                        queryset = base_queryset.filter(email=value)
                    else:
                        queryset = base_queryset.filter(username=value)
                    if queryset.exists():
                        raise CustomException(
                            errors=[f"{field} in use"],
                            message=f"The specified {field.replace('_', ' ')} is already in use by another user",
                        )

            self.manipulate_request_data_for_email_phone_number_changes(request)

            serializer = self.serializer_class.Update(
                instance=request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer = self.serializer_class.Retrieve(instance=request.user)
            return response.Response(status=status.HTTP_200_OK, data=serializer.data)
        else:
            instance = request.user
            instance.delete()
            raise CustomException(status_code=status.HTTP_204_NO_CONTENT)

    
    
    @decorators.action(
        detail=False,
        methods=["patch"],
        name="set_username",
        url_path="me/set_username",
    )
    def set_username(self, request, *args, **kwargs):
        if request.method == "PATCH":
            self.generate_username(request)
            serializer = self.serializer_class.Update(
                instance=request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer = self.serializer_class.Retrieve(instance=request.user)
            return response.Response(status=status.HTTP_200_OK, data=serializer.data)

    @decorators.action(detail=False, methods=["post"])
    def logout(self, request, *args, **kwargs):
        try:
            UserSession.objects.get(refresh=request.data.get("refresh")).delete()
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return response.Response(status=status.HTTP_205_RESET_CONTENT)
        except TokenError as err:
            raise CustomException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=str(err),
                errors=["refresh token error"],
            )
    
    
    @decorators.action(detail=False, methods=["post"])
    def change_password(self, request, *args, **kwargs):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        instance = request.user
        if not check_password(old_password, instance.password):
            raise CustomException(
                message="The old password you provided is incorrect",
                errors=["incorrect old password"],
            )

        if check_password(new_password, instance.password):
            raise CustomException(
                message="The new password must be different from the old passwords",
                errors=["same password"],
            )

        old_passwords = orjson.loads(instance.old_passwords or orjson.dumps([]))
        if new_password in old_passwords:
            raise CustomException(
                errors=["password already used before"],
                message="The new password has been used before on this account",
            )

        instance.set_password(new_password)
        old_passwords.append(old_password)
        instance.old_passwords = orjson.dumps(old_passwords)
        instance.save()
        return response.Response(
            status=status.HTTP_200_OK,
            data={"message": "Password changed successfully"},
        )

    
    
    
    @decorators.action(detail=False, methods=["post"])
    def set_password(self, request, *args, **kwargs):
        password = request.data.get("password")
        instance = request.user
        if instance.is_password_set:
            raise CustomException(
                message="The password of this account has already been set",
                errors=["password already set"],
            )

        instance.set_password(password)
        instance.is_password_set = True
        instance.save()
        return response.Response(
            status=status.HTTP_200_OK,
            data={"message": "Operation Successful"},
        )

    @decorators.action(
        detail=False, name="delete_user", url_path="me/delete_user", methods=["delete"]
    )
    def delete_user(self, request, *args, **kwargs):
        instance = request.user
        password = request.data.get("password")

        if not check_password(password, instance.password):
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST, data={"message": "Invalid password"}
            )

        else:

            instance.delete()
            return response.Response(
                status=status.HTTP_200_OK,
                data={"message": "user deleted account successfully!"},
            )



class AgentViewSet(viewsets.ViewSet):
    permission_classes = [AgentPermission]
    serializer_class = serializers.AgentSerializer

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                agent = Agent.objects.create(
                    first_name=request.data.get("first_name"),
                    last_name=request.data.get("last_name"),
                    phone_number=request.data.get("phone_number"),
                    email=request.data.get("email"),
                    address=request.data.get("address"),
                    lga=request.data.get("lga"),
                    ward=request.data.get("ward"),
                    market=request.data.get("market"),
                    transport=request.data.get("transport"),
                    account_number=request.data.get("account_number"),
                    bank_name=request.data.get("bank_name"),
                )
                serialized_agent = serializers.AgentSerializer(agent)
                return Response(
                    data={"message": "Agent created successfully", "status": status.HTTP_201_CREATED},
                )

        except Exception as e:
            return Response(
                data={"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
            )

    def list(self, request, *args, **kwargs):
        try:
            queryset = Agent.objects.all()
            serializer = serializers.AgentSerializer(queryset, many=True)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                data={"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
            )


    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            queryset = Agent.objects.get(id=pk)
            serializer = serializers.AgentSerializer(queryset)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                data={"message": "Agent does not exist", "status": status.HTTP_404_NOT_FOUND}
            )
        
    
    def update(self, request, pk=None, *args, **kwargs):
        try:
            queryset = Agent.objects.get(id=pk)
            serializer = serializers.AgentSerializer(queryset, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                )
            return Response(
                data={"message": "Invalid data", "status": status.HTTP_400_BAD_REQUEST}
            )
        except Exception as e:
            return Response(
                data={"message": "Error updating agent", "status": status.HTTP_400_BAD_REQUEST}
            )
        

    def destroy(self, request, pk=None, *args, **kwargs):
        try:
            queryset = Agent.objects.get(id=pk)
            queryset.delete()
            return Response(
                data={"message": "Agent deleted successfully", "status": status.HTTP_204_NO_CONTENT}
            )
        except Exception as e:
            return Response(
                data={"message": "Agent does not exist", "status": status.HTTP_404_NOT_FOUND}
            )
        
        


class EnforcerViewSet(viewsets.ViewSet):
    permission_classes = [EnforcerPermission]
    serializer_class = serializers.EnforcerSerializer

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                enforcer = Enforcer.objects.create(
                    first_name=request.data.get("first_name"),
                    last_name=request.data.get("last_name"),
                    phone_number=request.data.get("phone_number"),
                    email=request.data.get("email"),
                    address=request.data.get("address"),
                    lga=request.data.get("lga"),
                    ward=request.data.get("ward"),
                    market=request.data.get("market"),
                    transport=request.data.get("transport"),
                    account_number=request.data.get("account_number"),
                    bank_name=request.data.get("bank_name"),
                )
                serialized_enforcer = serializers.EnforcerSerializer(enforcer)
                return Response(
                    data={"message": "Enforcer created successfully", "status": status.HTTP_201_CREATED},
                )

        except Exception as e:
            return Response(
                data={"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
            )

    def list(self, request, *args, **kwargs):
        try:
            queryset = Enforcer.objects.all()
            serializer = serializers.EnforcerSerializer(queryset, many=True)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                data={"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
            )


    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            queryset = Enforcer.objects.get(id=pk)
            serializer = serializers.EnforcerSerializer(queryset)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                data={"message": "Enforcer does not exist", "status": status.HTTP_404_NOT_FOUND}
            )
        
    
    def update(self, request, pk=None, *args, **kwargs):
        try:
            queryset = Enforcer.objects.get(id=pk)
            serializer = serializers.EnforcerSerializer(queryset, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    data=serializer.data,
                    status=status.HTTP_200_OK,
                )
            return Response(
                data={"message": "Invalid data", "status": status.HTTP_400_BAD_REQUEST}
            )
        except Exception as e:
            return Response(
                data={"message": "Error updating enforcer", "status": status.HTTP_400_BAD_REQUEST}
            )
        

    def destroy(self, request, pk=None, *args, **kwargs):
        try:
            queryset = Enforcer.objects.get(id=pk)
            queryset.delete()
            return Response(
                data={"message": "Enforcer deleted successfully", "status": status.HTTP_204_NO_CONTENT}
            )
        except Exception as e:
            return Response(
                data={"message": "Enforcer does not exist", "status": status.HTTP_404_NOT_FOUND}
            )
        
        


