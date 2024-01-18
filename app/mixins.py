import inspect
from abc import ABC, abstractmethod

from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Manager, Model

from rest_framework import status, decorators
from rest_framework.response import Response
from app import permissions

from app.custom_exception import CustomException


UserModel = get_user_model()


class CustomRequestDataValidationMixin(ABC):
    @abstractmethod
    def get_required_fields(self):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)
            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(
                    self, request.method.lower(), self.http_method_not_allowed
                )
            else:
                handler = self.http_method_not_allowed
            if request.method.lower() in ["post", "patch", "put", "delete", "get"]:
                errors = []
                if request.method.lower() == "get":
                    data = request.GET
                else:
                    data = request.data
                required_fields_res = self.get_required_fields()
                assert callable(required_fields_res) or getattr(
                    required_fields_res, "__iter__"
                ), "'get_required_fields' method must return an iterable or callable"
                if callable(required_fields_res):
                    _, msg = required_fields_res(data)
                    if not _:
                        errors.append(msg)
                else:
                    for field in self.get_required_fields():
                        if not data.get(field):
                            errors.append(f"'{field}' is required")
                if errors:
                    response = Response(
                        data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    response = handler(request, *args, **kwargs)
            else:
                response = handler(request, *args, **kwargs)
        except Exception as exc:
            response = self.handle_exception(exc)
        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response


class CountListResponseMixin:
    def list(self, request, *args, **kwargs):
        if request.GET.get("count", "").lower() == "true":
            return Response(
                status=status.HTTP_200_OK,
                data={"count": self.filter_queryset(self.get_queryset()).count()},
            )
        return super().list(request, *args, **kwargs)


class BatchDestroyMixin:
    def validate_request_data(self, request_data):
        items = request_data.get("items")
        exclude = request_data.get("exclude")
        if (items is not None) or (exclude is not None):
            print(items, exclude, type(items))
            if items and exclude:
                return False, "you cannot specify both 'items' and 'exclude' together"
            if items is None:
                if type(exclude) != list:
                    return False, "'exclude' must be a list of indexes"
            else:
                if type(items) != list and items != "__all__":
                    return False, "'items' must be a list of indexes or '__all__'"
            return True, None
        return False, "either 'items' or 'exclude' is required"

    def get_required_fields(self):
        if self.action == "bulk_delete":
            return lambda request_data: self.validate_request_data(request_data)
        return []

    def get_bulk_delete_queryset(self):
        assert self.queryset, "queryset must be defined"
        auth_user = self.request.user
        if not auth_user.is_authenticated:
            return self.queryset.empty()
        if auth_user.is_super_admin:
            return self.queryset
        else:
            view_cls_model = (
                self.queryset.model
                if (
                    isinstance(self.queryset, QuerySet)
                    or isinstance(self.queryset, Manager)
                )
                else (
                    inspect.isclass(self.queryset)
                    and issubclass(self.queryset, Model)
                    and self.queryset
                )
            )
            if view_cls_model and getattr(view_cls_model, "owner", None):
                return self.queryset.filter(owner=self.request.user)
            raise CustomException(
                errors=[f"unsupported operation"],
                message=f"This resource does not support deletion by a user",
            )

    @decorators.action(detail=False, methods=["post"])
    def bulk_delete(self, request, *args, **kwargs):
        queryset = self.get_bulk_delete_queryset()
        if request.data.get("items"):
            if request.data["items"] == "__all__":
                objects_to_delete = queryset.all()
            else:
                objects_to_delete = queryset.filter(id__in=request.data["items"])
        else:
            objects_to_delete = queryset.exclude(id__in=request.data["exclude"])
        found_objects_indexes_to_delete = list(
            objects_to_delete.values_list("id", flat=True)
        )
        objects_to_delete.delete()
        return Response(
            status=status.HTTP_200_OK,
            data={"items_deleted": found_objects_indexes_to_delete},
        )


class ReadAllWriteAdminOnlyPermissionMixin:
    def get_permissions(self):
        if self.action not in ["list", "retrieve"]:
            return super().get_permissions() + [permissions.IsAccountType.AdminUser()]
        return super().get_permissions()


class WriteAllReadAdminOnlyPermissionMixin:
    def get_permissions(self):
        if self.action not in ["create"]:
            return super().get_permissions() + [permissions.IsAccountType.AdminUser()]
        # This means all users will able to contact the admin.
        return []


class ReadAdminOnlyWriteAdminOnlyPermissionMixin:
    def get_permissions(self):
        return super().get_permissions() + [permissions.IsAccountType.AdminUser()]


class GuestReadAllWriteAdminOnlyPermissionMixin:
    def get_permissions(self):
        print("Permissions")
        if self.action not in ["list", "retrieve"]:
            print(permissions.IsAccountType.AdminUser(), "You must be admin")
            return super().get_permissions() + [permissions.IsAccountType.AdminUser()]
        return []


class ManageManyToManyMixin:
    def manage_usermodel_many_to_many(
        self, instance, user_ids, attr, type_="add"
    ) -> list[int] | None:
        if user_ids:
            users = []
            present_users = []

            if type_ == "add":
                for user_id in user_ids:
                    try:
                        user = UserModel.objects.get(id=user_id)
                        users.append(user)
                    except UserModel.DoesNotExist:
                        pass

                get_instance_attr = getattr(instance, attr)
                get_instance_attr.add(*users)
                return None

            elif type_ == "remove":
                instance_object = getattr(instance, attr)
                for user_id in user_ids:
                    try:
                        user = instance_object.get(id=user_id)
                        users.append(user)
                        present_users.append(user_id)
                    except Exception:
                        pass

                get_instance_attr = getattr(instance, attr)
                get_instance_attr.remove(*users)
                return present_users


class ViewSetHelper:
    def retrieve_from_instance(self):
        instance = self.get_queryset()
        serializer = self.serializer_class(instance=instance)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class FilterBackendPropertiesMixin:
    @property
    def filterset_fields(self):
        return getattr(self.get_serializer_class().Meta, "filterset_fields", [])

    @property
    def ordering_fields(self):
        return getattr(self.get_serializer_class().Meta, "ordering_fields", [])

    @property
    def search_fields(self):
        return getattr(self.get_serializer_class().Meta, "search_fields", [])