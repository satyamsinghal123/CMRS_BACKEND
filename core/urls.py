from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, BankAccountViewSet, health_check
from .views import (
    BranchViewSet,
    BankAccountViewSet,
    health_check,
    seed_demo_data,
)
router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branches")
router.register("bank-accounts", BankAccountViewSet, basename="bank-accounts")

urlpatterns = [path("health/", health_check, name="health"), path("", include(router.urls)),
               path("seed/", seed_demo_data, name="seed-demo"),
               ]
