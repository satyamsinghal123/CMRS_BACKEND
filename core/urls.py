from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, BankAccountViewSet, health_check
<<<<<<< HEAD
from .views import (
    BranchViewSet,
    BankAccountViewSet,
    health_check,
    seed_demo_data,
)
=======

>>>>>>> 120e1d9eee648063b7d1519a57ed6c21f971a6a0
router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branches")
router.register("bank-accounts", BankAccountViewSet, basename="bank-accounts")

<<<<<<< HEAD
urlpatterns = [path("health/", health_check, name="health"), path("", include(router.urls)),
               path("seed/", seed_demo_data, name="seed-demo"),
               ]
=======
urlpatterns = [path("health/", health_check, name="health"), path("", include(router.urls))]
>>>>>>> 120e1d9eee648063b7d1519a57ed6c21f971a6a0
