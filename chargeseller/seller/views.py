from django.shortcuts import render
from rest_framework import viewsets
from .models import Seller, CreditRequest
from .serializers import SellerSerializer, CreditRequestSerializer
from django.db import transaction

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
    



#TODO:
# - Implement all apis with logic
# - Implement permissions for requests
# - Implement race conditions for requests
# - Implement throttling for requests
# - Implement multiprocessing for requests with reddis
# - Implement spending double for requests with reddis
# - Implement tests for requests