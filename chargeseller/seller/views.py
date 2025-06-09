from django.shortcuts import render
from rest_framework import viewsets
from .models import Seller, CreditRequest, Transaction
from .serializers import SellerSerializer, CreditRequestSerializer, CreditRequestUpdateStatusSerializer
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from datetime import datetime


# Create your views here.


class SellerViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing seller instances.
    """

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

    queryset = CreditRequest.objects.all()
    serializer_class = CreditRequestSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], url_path="update-status", serializer_class=CreditRequestUpdateStatusSerializer)
    def update_status(self, request, pk=None):
        with transaction.atomic():
            credit_request = self.get_object()
            serializer = self.get_serializer(credit_request, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            # Check credit request status for balance
            if not (request.data['status'] == credit_request.status):
                if request.data['status'] == CreditRequest.REJECCTEDSTATUS and credit_request.status == CreditRequest.APPROVEDSTATUS:
                    credit_request.seller.balance -= credit_request.amount
                elif request.data['status'] == CreditRequest.APPROVEDSTATUS:
                    credit_request.seller.balance += credit_request.amount
                credit_request.is_processed = True
                serializer.save()
                credit_request.seller.save()
                Transaction.submit_transaction_for_credit_increase(credit_request=credit_request, user=request.user)



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
