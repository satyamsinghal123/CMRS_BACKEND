from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, BankAccountViewSet, health_check

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branches")
router.register("bank-accounts", BankAccountViewSet, basename="bank-accounts")

urlpatterns = [path("health/", health_check, name="health"), path("", include(router.urls))]
