from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"sellers", SellerViewSet, basename="seller")
router.register(r"credit-requests", CreditRequestViewSet, basename="credit-request")
router.register(r"phone-number", PhoneNumberViewset, basename="phone-number")
router.register(r"transactions", TransactionReadOnlyViewSet, basename="transactions")


urlpatterns = [
    path("", include(router.urls)),
    path("charge-orders/", ChargeOrderCreateView.as_view(), name="charge-order-create"),
    path(
        "charge-orders-list/", ChargeOrderListView.as_view(), name="charge-order-list"
    ),
]
