from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_simplejwt.views import TokenRefreshView

from .views import *

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

app_name = "user"
router.register("", AuthViewSet, basename="auth")
router.register(r'informal', InformalSectorViewSet, basename='informal')
router.register(r'agent', AgentViewSet, basename='agent')

urlpatterns = router.urls
urlpatterns += [
    path("login/", AuthLoginView.as_view(), name="auth_login"),
    path('admin_login/', AdminLoginViewSet.as_view(), name='admin_login'),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterUserView.as_view(), name="register"),
    path("validate_payment/", validate_payment, name="validate_payment"),
    path("markets/", MarketsViewSet.as_view(), name="markets"),
    path("transports/", TransportsViewSet.as_view(), name="transports"),
    path("wards/", WardsViewSet.as_view(), name="wards"),
    path("lgas/", LgaViewSet.as_view(), name="lgas"),
]