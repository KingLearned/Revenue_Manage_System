from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

from app.custom_utils import Utils
from . import date_time as DateTime
UserModel = get_user_model()
from . import enums




class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.user and request.user.is_staff


class AgentPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET' or request.method == 'PUT' or request.method == 'DELETE':
            if request.user.is_agent:
                return True
            else:
                return False
        return request.user and request.user.is_staff

class EnforcerPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET' or request.method == 'PUT' or request.method == 'DELETE':
            if request.user.is_enforcer:
                return True
            else:
                return False
        return request.user and request.user.is_staff


class IsGuestUser(BasePermission):
    """
    Allows access only to non-authenticated users.
    """

    message: str

    def has_permission(self, request, view):
        self.message = "You are already logged in"
        return not request.user.is_authenticated


class IsAccountType:
    class SuperAdminUser(BasePermission):
        """
        Allows access only to super admin users.
        """

        message: str

        def has_permission(self, request, view):
            self.message = "This endpoint is only for super admins"
            return (
                request.user.account_type
                == enums.UserAccountType.SUPER_ADMINISTRATOR.value
            )

    class AdminUser(BasePermission):
        """
        Allows access only to admin users.
        """

        message: str

        def has_permission(self, request, view):
            self.message = "You are not an admin!"
            return request.user.account_type in [
                enums.UserAccountType.ADMINISTRATOR.value,
                enums.UserAccountType.SUPER_ADMINISTRATOR.value,
            ]

    def AdminGroup(perms: tuple, group_name: str = None):
        class PermissionRequired(BasePermission):
            """Verify that the current user has all specified permissions."""

            def has_permission(self, request, view):
                """
                Override this method to customize the way permissions are checked.
                """
                self.message = "User selected is not an admin"

                data = request.GET if request.method.lower() == "get" else request.data
                if not data.get("admin"):
                    self.message = "admin is required!"
                    return False

                user = Utils.get_object_or_raise_error(UserModel, pk=data.get("admin"))

                self.message = "Permission denied"
                if group_name:
                    self.message += " ; Admin is not a %s" % group_name

                return (
                    user.has_perms(perms)
                    or user.account_type
                    == enums.UserAccountType.SUPER_ADMINISTRATOR.value
                )

        return PermissionRequired


class IsAnAdmin(BasePermission):
    """
    Allows access only to user gotten from request body is an admin.
    """

    message: str

    def has_permission(self, request, view):
        self.message = "User selected is not an admin"

        data = request.GET if request.method.lower() == "get" else request.data
        if not data.get("admin"):
            self.message = "admin is required!"
            return False

        user = Utils.get_object_or_raise_error(UserModel, pk=data.get("admin"))
        return user.account_type in [
            enums.UserAccountType.ADMINISTRATOR.value,
            enums.UserAccountType.SUPER_ADMINISTRATOR.value,
        ]


def GroupPermissions(perms: tuple, group_name: str = None):
    class PermissionRequired(BasePermission):
        """Verify that the current user has all specified permissions."""

        def has_permission(self, request, view):
            """
            Override this method to customize the way permissions are checked.
            """
            self.message = "Permission denied"
            if group_name:
                self.message += " ; You are not a %s admin" % group_name

            # for ss in perms:
            #     print(request.user.has_perm(ss), request.user)
            return (
                request.user.has_perms(perms)
                or request.user.account_type
                == enums.UserAccountType.SUPER_ADMINISTRATOR.value
            )

    return PermissionRequired