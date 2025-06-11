from rest_framework import serializers
from .models import Seller, CreditRequest, Transaction, PhoneNumber, ChargeOrder


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ["id", "user", "balance", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative.")
        return value


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = "__all__"


class CreditRequestSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(read_only=True, many=True)
    STATUS_MAP = {
        "1": "pending",
        "2": "approved",
        "3": "rejected",
    }

    class Meta:
        model = CreditRequest
        fields = [
            "id",
            "seller",
            "amount",
            "status",
            "is_processed",
            "created_at",
            "updated_at",
            "transactions",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "status",
            "transactions",
            "is_processed",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_seller(self, value):
        if not isinstance(value, Seller):
            raise serializers.ValidationError("Invalid seller instance.")
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        status_int = instance.status
        representation["status"] = self.STATUS_MAP.get(str(status_int), str(status_int))
        return representation


class CreditRequestUpdateStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[2, 3])

    STATUS_MAP = {
        "1": "pending",
        "2": "approved",
        "3": "rejected",
    }

    class Meta:
        model = CreditRequest
        fields = ["id", "seller", "amount", "status"]
        read_only_fields = ["id", "seller", "amount", "created_at", "updated_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        status_int = instance.status
        representation["status"] = self.STATUS_MAP.get(str(status_int), str(status_int))
        return representation


class PhoneNumberSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhoneNumber
        fields = ['id', 'phone_number', 'is_active']


class ChargeOrderSerializer(serializers.ModelSerializer):
    transaction = TransactionSerializer(read_only=True)

    class Meta:
        model = ChargeOrder
        fields = ['id', 'seller', 'phone_number', 'amount', 'error_message', 'retry_count','transaction']
        read_only_fields = ['id', 'error_message', 'retry_count', 'transaction']

    def validate_amount(self, value):

        if value <= 0:
            raise serializers.ValidationError("Amount cannot be negative or zero")
        return value

    def validate(self, attrs):
        seller = attrs.get('seller')
        amount = attrs.get('amount')

        try:
            seller_obj = Seller.objects.select_for_update().get(id=seller.id)
        except Seller.DoesNotExist:
            raise serializers.ValidationError({
                'seller': 'Seller with this ID does not exist'
            })
        except AttributeError:
            raise serializers.ValidationError({
                'seller': 'Seller field is required'
            })
    
        # Check Seller Balance
        if seller and amount:
            seller_obj = Seller.objects.select_for_update().get(id=seller.id)
            if seller_obj.balance < amount:
                raise serializers.ValidationError("Insufficient seller balance")
        
        return attrs