from django.shortcuts import render
from rest_framework import viewsets
from .models import Seller, CreditRequest
from .serializers import SellerSerializer, CreditRequestSerializer, CreditRequestUpdateStatusSerializer
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action


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
    @transaction.atomic
    def update_status(self, request, pk=None):
        credit_request = self.get_object()
        serializer = self.get_serializer(credit_request, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# TODO:
# - Implement all apis with logic
# - Implement permissions for requests
# - Implement race conditions for requests
# - Implement throttling for requests
# - Implement multiprocessing for requests with reddis
# - Implement spending double for requests with reddis
# - Implement tests for requests
