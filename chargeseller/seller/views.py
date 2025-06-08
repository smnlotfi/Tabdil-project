from django.shortcuts import render
from rest_framework import viewsets
from .models import Seller, CreditRequest
from .serializers import SellerSerializer, CreditRequestSerializer
# Create your views here.

class SellerViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing seller instances.
    """
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer  

class CreditRequestViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing credit request instances.
    """
    queryset = CreditRequest.objects.all()
    serializer_class = CreditRequestSerializer