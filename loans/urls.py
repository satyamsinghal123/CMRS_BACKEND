from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import LoanViewSet, RepaymentScheduleViewSet, collection_tasks

router = DefaultRouter()
router.register("loans", LoanViewSet, basename="loans")
router.register("schedules", RepaymentScheduleViewSet, basename="schedules")

urlpatterns = [path("collection-tasks/", collection_tasks, name="collection-tasks"), path("", include(router.urls))]
