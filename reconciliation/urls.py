from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ReconciliationViewSet

router = DefaultRouter()
router.register("reconciliation", ReconciliationViewSet, basename="reconciliation")

urlpatterns = [path("", include(router.urls))]
