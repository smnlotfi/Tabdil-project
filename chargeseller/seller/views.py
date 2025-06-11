from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from .models import Seller, CreditRequest, Transaction, PhoneNumber, ChargeOrder
from .serializers import (
    SellerSerializer,
    CreditRequestSerializer,
    CreditRequestUpdateStatusSerializer,
    PhoneNumberSerializer,
    ChargeOrderSerializer,
    TransactionSerializer,
)
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from core.permission import IsSellerUser
from django.db.models import F
import logging
from drf_spectacular.utils import extend_schema


logger = logging.getLogger(__name__)


class SellerViewSet(viewsets.ModelViewSet):

    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class CreditRequestViewSet(viewsets.ModelViewSet):

    queryset = CreditRequest.objects.select_for_update().select_related("seller")
    serializer_class = CreditRequestSerializer
    permission_classes = [IsSellerUser]

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

            if request.data["status"] == CreditRequest.REJECCTEDSTATUS:
                Seller.objects.filter(id=credit_request.seller.id).update(
                    balance=F("balance") - credit_request.amount
                )
            elif request.data["status"] == CreditRequest.APPROVEDSTATUS:
                Seller.objects.filter(id=credit_request.seller.id).update(
                    balance=F("balance") + credit_request.amount
                )

            # If you Want Update Status Api Should Be Editable Use This Code
            # if request.data["status"] != credit_request.status:
            #     if (
            #         request.data["status"] == CreditRequest.REJECCTEDSTATUS
            #         and credit_request.status == CreditRequest.APPROVEDSTATUS
            #     ):
            #         Seller.objects.filter(id=credit_request.seller.id).update(
            #             balance=F("balance") - credit_request.amount
            #         )
            #     elif request.data["status"] == CreditRequest.APPROVEDSTATUS:
            #         Seller.objects.filter(id=credit_request.seller.id).update(
            #             balance=F("balance") + credit_request.amount
            #         )

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


class PhoneNumberViewset(viewsets.ModelViewSet):

    queryset = PhoneNumber.objects.all()
    serializer_class = PhoneNumberSerializer
    permission_classes = [IsSellerUser]


class ChargeOrderCreateView(APIView):
    permission_classes = [IsSellerUser]

    @extend_schema(request=ChargeOrderSerializer)
    @transaction.atomic
    def post(self, request):
        try:
            serializer = ChargeOrderSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            seller_id = serializer.validated_data["seller"].id
            phone_number = serializer.validated_data["phone_number"]
            amount = serializer.validated_data["amount"]

            # 1-Check For Recent Duplicate Request
            recent_order = ChargeOrder.get_recent_order(seller_id, phone_number, amount)

            # 2-Increment Retry Count
            if recent_order:
                recent_order.retry_count += 1
                recent_order.error_message = f"Duplicate request attempt. Retry count: {recent_order.retry_count}"
                recent_order.save(
                    update_fields=["retry_count", "error_message", "updated_at"]
                )

                return Response(
                    {
                        "error": "Duplicate request found within 10 minutes",
                        "recent_order_id": recent_order.id,
                        "retry_count": recent_order.retry_count,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 3-Create New Charge Order
            charge_order = serializer.save()
            # 2-Update Seller Balance And Create Transaction
            try:
                seller = Seller.objects.select_for_update().get(id=seller_id)
                balance_before = seller.balance
                seller.balance = F("balance") - amount
                seller.save(update_fields=["balance"])
                seller.refresh_from_db()
                balance_after = seller.balance

            except Seller.DoesNotExist:
                return Response(
                    {"error": "Seller not found"}, status=status.HTTP_404_NOT_FOUND
                )
            Transaction.submit_transaction_for_charge_order(
                charge_order=charge_order,
                seller=seller,
                user=request.user,
                balance_after=balance_after,
                balance_before=balance_before,
            )

            logger.info(f"Charge order created successfully: {charge_order.id}")

            return Response(
                ChargeOrderSerializer(charge_order).data, status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error creating charge order: {str(e)}")


class ChargeOrderListView(APIView):
    permission_classes = [IsSellerUser]

    def get(self, request):
        queryset = ChargeOrder.objects.select_related("seller", "phone_number").filter(
            seller=request.user.seller
        )

        serializer = ChargeOrderSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TransactionReadOnlyViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):

    queryset = Transaction.objects.select_related(
        "seller", "phone_number", "credit_request", "charge_order"
    ).all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        transaction_type = self.request.query_params.get("type", None)
        seller = self.request.query_params.get("seller", None)
        phone_number = self.request.query_params.get("phone_number", None)

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        if seller:
            queryset = queryset.filter(seller=seller)

        if phone_number:
            queryset = queryset.filter(phone_number=phone_number)

        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        from django.db.models import Count, Sum

        summary = (
            self.get_queryset()
            .values("transaction_type")
            .annotate(
                count=Count("id"),
                total_amount=Sum("amount"),  # Assuming you have an amount field
            )
        )

        return Response(summary)


# TODO:
# - Implement all apis with logic
# - Implement permissions for requests
# - Implement race conditions for requests
# - Implement spending double for requests with reddis
# - Implement multiprocessing for requests with reddis
# - Implement tests for requests
