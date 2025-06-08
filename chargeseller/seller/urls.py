
from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'sellers', SellerViewSet, basename='seller')
router.register(r'credit-requests', CreditRequestViewSet, basename='credit-request')


urlpatterns = [
    path('', include(router.urls)),
]
