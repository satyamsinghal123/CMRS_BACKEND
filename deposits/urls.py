from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BankDepositViewSet, SettlementViewSet

router = DefaultRouter()
router.register("deposits", BankDepositViewSet, basename="deposits")
router.register("settlements", SettlementViewSet, basename="settlements")

urlpatterns = [path("", include(router.urls))]
