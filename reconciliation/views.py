from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Reconciliation
from .serializers import ReconciliationSerializer
from accounts.models import Role
from accounts.permissions import IsManagerOrOperations

class ReconciliationViewSet(viewsets.ModelViewSet):
    queryset = Reconciliation.objects.select_related("submission", "branch", "reviewed_by").all()
    serializer_class = ReconciliationSerializer
    permission_classes = [IsManagerOrOperations]
    filterset_fields = ["branch", "status"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        if request.user.role not in {Role.ADMIN, Role.BRANCH_MANAGER}:
            return Response({"detail": "Only branch managers can approve reconciliation."}, status=403)
        item = self.get_object()
        if item.status != "PENDING":
            return Response({"detail": "Only pending records can be approved."}, status=400)
        item.lock(request.user)
        item.submission.status = "APPROVED"
        item.submission.reviewed_by = request.user
        item.submission.reviewed_at = timezone.now()
        item.submission.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        from cashcollections.models import Repayment
        Repayment.objects.filter(agent=item.submission.agent, branch=item.branch, status=Repayment.Status.SUBMITTED).update(status=Repayment.Status.RECONCILED)
        return Response(self.get_serializer(item).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        if request.user.role not in {Role.ADMIN, Role.BRANCH_MANAGER}:
            return Response({"detail": "Only branch managers can reject reconciliation."}, status=403)
        item = self.get_object()
        if item.status != "PENDING":
            return Response({"detail": "Only pending records can be rejected."}, status=400)
        item.status = "REJECTED"
        item.manager_notes = request.data.get("notes", item.manager_notes)
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.save()
        item.submission.status = "REJECTED"
        item.submission.reviewed_by = request.user
        item.submission.reviewed_at = timezone.now()
        item.submission.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        from cashcollections.models import Repayment
        Repayment.objects.filter(agent=item.submission.agent, branch=item.branch, status=Repayment.Status.SUBMITTED).update(status=Repayment.Status.COLLECTED)
        return Response(self.get_serializer(item).data)
