from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import RepaymentViewSet, AgentCashSubmissionViewSet, CollectionAttemptViewSet

router = DefaultRouter()
router.register("repayments", RepaymentViewSet, basename="repayments")
router.register("submissions", AgentCashSubmissionViewSet, basename="submissions")
router.register("collection-attempts", CollectionAttemptViewSet, basename="collection-attempts")

urlpatterns = [path("", include(router.urls))]
