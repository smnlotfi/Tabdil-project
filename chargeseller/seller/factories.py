# factories.py
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import User, Seller, CreditRequest, PhoneNumber, ChargeOrder, Transaction

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_seller = True
    is_active = True


class SellerFactory(DjangoModelFactory):
    class Meta:
        model = Seller

    user = factory.SubFactory(UserFactory)
    balance = factory.LazyFunction(lambda: Decimal("1000.00"))


class CreditRequestFactory(DjangoModelFactory):
    class Meta:
        model = CreditRequest

    seller = factory.SubFactory(SellerFactory)
    amount = factory.LazyFunction(lambda: Decimal("100.00"))
    status = CreditRequest.PENDINGSTATUS
    is_processed = False


class PhoneNumberFactory(DjangoModelFactory):
    class Meta:
        model = PhoneNumber

    phone_number = factory.Sequence(lambda n: f"0912345{n:04d}")
    is_active = True


class ChargeOrderFactory(DjangoModelFactory):
    class Meta:
        model = ChargeOrder

    seller = factory.SubFactory(SellerFactory)
    phone_number = factory.SubFactory(PhoneNumberFactory)
    amount = factory.LazyFunction(lambda: Decimal("50.00"))
    error_message = ""
    retry_count = 0


class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    seller = factory.SubFactory(SellerFactory)
    transaction_type = 1  # Credit_Increase
    amount = factory.LazyFunction(lambda: Decimal("100.00"))
    status = Transaction.PENDINGSTATUS
    reference_id = factory.Faker("uuid4")
    balance_before = factory.LazyFunction(lambda: Decimal("1000.00"))
    balance_after = factory.LazyFunction(lambda: Decimal("1100.00"))
