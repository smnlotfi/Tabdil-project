from django.shortcuts import render
from rest_framework import viewsets
from .models import Seller, CreditRequest, Transaction
from .serializers import (
    SellerSerializer,
    CreditRequestSerializer,
    CreditRequestUpdateStatusSerializer,
)
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from core.permission import IsSellerUser
from django.db.models import F

# Create your views here.


class SellerViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing seller instances.
    """

    permission_classes = [IsAdminUser]

    queryset = Seller.objects.all()
    serializer_class = SellerSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class CreditRequestViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing credit request instances.
    """

    permission_classes = [IsSellerUser]

    queryset = CreditRequest.objects.select_for_update().select_related("seller")
    serializer_class = CreditRequestSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["patch"],
        url_path="update-status",
        serializer_class=CreditRequestUpdateStatusSerializer,
        permission_classes=[IsAdminUser],
    )
    def update_status(self, request, pk=None):
        with transaction.atomic():
            credit_request = (
                CreditRequest.objects.select_for_update().filter(pk=pk).first()
            )

            if not credit_request:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if credit_request.is_processed:
                return Response(
                    {"error": "This credit request has already been processed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(
                credit_request, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)

            balance_before = credit_request.seller.balance

            if request.data["status"] != credit_request.status:
                if (
                    request.data["status"] == CreditRequest.REJECCTEDSTATUS
                    and credit_request.status == CreditRequest.APPROVEDSTATUS
                ):
                    Seller.objects.filter(id=credit_request.seller.id).update(
                        balance=F("balance") - credit_request.amount
                    )
                elif request.data["status"] == CreditRequest.APPROVEDSTATUS:
                    Seller.objects.filter(id=credit_request.seller.id).update(
                        balance=F("balance") + credit_request.amount
                    )

            credit_request.seller.refresh_from_db()
            balance_after = credit_request.seller.balance

            credit_request.is_processed = True
            serializer.save()

            Transaction.submit_transaction_for_credit_increase(
                credit_request=credit_request,
                user=request.user,
                balance_after=balance_after,
                balance_before=balance_before,
            )

        data = CreditRequestSerializer(credit_request).data
        return Response(data, status=status.HTTP_200_OK)


# TODO:
# - Implement all apis with logic
# - Implement permissions for requests
# - Implement race conditions for requests
# - Implement throttling for requests
# - Implement multiprocessing for requests with reddis
# - Implement spending double for requests with reddis
# - Implement tests for requests
