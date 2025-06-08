from rest_framework import serializers
from .models import Seller, CreditRequest


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative.")
        return value

    
class CreditRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRequest
        fields = ['id', 'seller', 'amount', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_seller(self, value):
        if not isinstance(value, Seller):
            raise serializers.ValidationError("Invalid seller instance.")
        return value

