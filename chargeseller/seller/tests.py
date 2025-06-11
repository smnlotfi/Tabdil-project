import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from django.db import transaction
from .factories import (
    UserFactory,
    SellerFactory,
    CreditRequestFactory,
    PhoneNumberFactory,
    ChargeOrderFactory,
)
from .models import CreditRequest, Seller

BASE_URL = "http://127.0.01:8000"


class CreditRequestAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.seller1 = SellerFactory(balance=Decimal("2000.00"))
        self.seller2 = SellerFactory(balance=Decimal("1500.00"))

        self.user1 = self.seller1.user
        self.user2 = self.seller2.user

        self.credit_amounts = [
            Decimal("100.00"),
            Decimal("250.00"),
            Decimal("500.00"),
            Decimal("750.00"),
            Decimal("1000.00"),
        ]

    def test_create_credit_requests_seller1(self):
        self.client.force_authenticate(user=self.user1)
        initial_balance = self.seller1.balance

        for amount in self.credit_amounts:
            data = {"seller": self.seller1.id, "amount": str(amount)}
            response = self.client.post(f"{BASE_URL}/credit-requests/", data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Decimal(response.data["amount"]), amount)
            self.assertEqual(response.data["seller"], self.seller1.id)
            self.assertEqual(response.data["status"], "pending")

            self.seller1.refresh_from_db()
            self.assertEqual(self.seller1.balance, initial_balance)

    def test_create_credit_requests_seller2(self):
        self.client.force_authenticate(user=self.user2)
        initial_balance = self.seller2.balance

        for amount in self.credit_amounts:
            data = {"seller": self.seller2.id, "amount": str(amount)}
            response = self.client.post(f"{BASE_URL}/credit-requests/", data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Decimal(response.data["amount"]), amount)
            self.assertEqual(response.data["seller"], self.seller2.id)
            self.assertEqual(response.data["status"], "pending")

            self.seller2.refresh_from_db()
            self.assertEqual(self.seller2.balance, initial_balance)

    def test_list_credit_requests_seller1(self):
        self.client.force_authenticate(user=self.user1)
        initial_balance = self.seller1.balance

        for amount in self.credit_amounts:
            CreditRequestFactory(seller=self.seller1, amount=amount)

        response = self.client.get(f"{BASE_URL}/credit-requests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        self.seller1.refresh_from_db()
        self.assertEqual(self.seller1.balance, initial_balance)

    def test_list_credit_requests_seller2(self):
        self.client.force_authenticate(user=self.user2)
        initial_balance = self.seller2.balance

        for amount in self.credit_amounts:
            CreditRequestFactory(seller=self.seller2, amount=amount)

        response = self.client.get(f"{BASE_URL}/credit-requests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        self.seller2.refresh_from_db()
        self.assertEqual(self.seller2.balance, initial_balance)

    def test_retrieve_credit_request_seller1(self):
        self.client.force_authenticate(user=self.user1)
        initial_balance = self.seller1.balance

        credit_request = CreditRequestFactory(
            seller=self.seller1, amount=self.credit_amounts[0]
        )

        response = self.client.get(f"{BASE_URL}/credit-requests/{credit_request.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], credit_request.id)
        self.assertEqual(Decimal(response.data["amount"]), self.credit_amounts[0])

        self.seller1.refresh_from_db()
        self.assertEqual(self.seller1.balance, initial_balance)

    def test_retrieve_credit_request_seller2(self):
        self.client.force_authenticate(user=self.user2)
        initial_balance = self.seller2.balance

        credit_request = CreditRequestFactory(
            seller=self.seller2, amount=self.credit_amounts[1]
        )

        response = self.client.get(f"{BASE_URL}/credit-requests/{credit_request.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], credit_request.id)
        self.assertEqual(Decimal(response.data["amount"]), self.credit_amounts[1])

        self.seller2.refresh_from_db()
        self.assertEqual(self.seller2.balance, initial_balance)


def create_credit_request_worker(seller_data, amount, base_url):
    from django.test import Client
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=seller_data["user"])

    data = {"seller": seller_data["seller_id"], "amount": str(amount)}

    response = client.post(f"{base_url}/credit-requests/", data)

    return {
        "status_code": response.status_code,
        "amount": response.data.get("amount") if response.status_code == 201 else None,
        "seller_id": (
            response.data.get("seller") if response.status_code == 201 else None
        ),
        "status": response.data.get("status") if response.status_code == 201 else None,
        "worker_amount": amount,
        "worker_seller_id": seller_data["seller_id"],
    }


class CreditRequestParallelAPITestCase(TransactionTestCase):
    def setUp(self):
        self.seller1 = SellerFactory(balance=Decimal("2000.00"))
        self.seller2 = SellerFactory(balance=Decimal("1500.00"))

        self.seller1_data = {
            "user": self.seller1.user,
            "seller_id": self.seller1.id,
            "initial_balance": self.seller1.balance,
        }

        self.seller2_data = {
            "user": self.seller2.user,
            "seller_id": self.seller2.id,
            "initial_balance": self.seller2.balance,
        }

        self.credit_amounts = [
            Decimal("100.00"),
            Decimal("250.00"),
            Decimal("500.00"),
            Decimal("750.00"),
            Decimal("1000.00"),
        ]

        self.base_url = BASE_URL

    def test_parallel_create_credit_requests_both_sellers(self):
        initial_seller1_balance = self.seller1.balance
        initial_seller2_balance = self.seller2.balance

        tasks = []

        for amount in self.credit_amounts:
            tasks.append((self.seller1_data, amount, self.base_url))
            tasks.append((self.seller2_data, amount, self.base_url))

        with ProcessPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(create_credit_request_worker, *task) for task in tasks
            ]
            results = [future.result() for future in as_completed(futures)]

        seller1_results = [
            r for r in results if r["worker_seller_id"] == self.seller1.id
        ]
        seller2_results = [
            r for r in results if r["worker_seller_id"] == self.seller2.id
        ]

        self.assertEqual(len(seller1_results), 5)
        self.assertEqual(len(seller2_results), 5)

        for result in seller1_results:
            self.assertEqual(result["status_code"], status.HTTP_201_CREATED)
            self.assertEqual(result["seller_id"], self.seller1.id)
            self.assertEqual(result["status"], "pending")
            self.assertEqual(Decimal(result["amount"]), result["worker_amount"])

        for result in seller2_results:
            self.assertEqual(result["status_code"], status.HTTP_201_CREATED)
            self.assertEqual(result["seller_id"], self.seller2.id)
            self.assertEqual(result["status"], "pending")
            self.assertEqual(Decimal(result["amount"]), result["worker_amount"])

        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()

        self.assertEqual(self.seller1.balance, initial_seller1_balance)
        self.assertEqual(self.seller2.balance, initial_seller2_balance)
        self.assertEqual(self.seller1.balance, self.seller1_data["initial_balance"])
        self.assertEqual(self.seller2.balance, self.seller2_data["initial_balance"])

        seller1_from_db = Seller.objects.get(id=self.seller1.id)
        seller2_from_db = Seller.objects.get(id=self.seller2.id)

        self.assertEqual(seller1_from_db.balance, Decimal("2000.00"))
        self.assertEqual(seller2_from_db.balance, Decimal("1500.00"))

        self.assertNotEqual(seller1_from_db.balance, Decimal("0.00"))
        self.assertNotEqual(seller2_from_db.balance, Decimal("0.00"))
        self.assertGreater(seller1_from_db.balance, Decimal("0.00"))
        self.assertGreater(seller2_from_db.balance, Decimal("0.00"))


class ChargeOrderAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.seller1 = SellerFactory(balance=Decimal("1000000.00"))
        self.seller2 = SellerFactory(balance=Decimal("3000.00"))

        self.user1 = self.seller1.user
        self.user2 = self.seller2.user

        self.phone1 = PhoneNumberFactory(phone_number="09123456789")
        self.phone2 = PhoneNumberFactory(phone_number="09123456790")
        self.phone3 = PhoneNumberFactory(phone_number="09123456791")

        self.charge_amounts = [Decimal(str(i + 1)) for i in range(1000)]

    def test_create_1000_charge_orders_seller1(self):
        self.client.force_authenticate(user=self.user1)
        initial_balance = self.seller1.balance

        for amount in self.charge_amounts:
            data = {
                "seller": self.seller1.id,
                "phone_number": self.phone1.id,
                "amount": str(amount),
            }
            response = self.client.post(f"{BASE_URL}/charge-orders/", data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Decimal(response.data["amount"]), amount)
            self.assertEqual(response.data["seller"], self.seller1.id)
            self.assertEqual(response.data["phone_number"], self.phone1.id)

            self.seller1.refresh_from_db()
            initial_balance -= amount
            self.assertEqual(self.seller1.balance, initial_balance)

    def test_list_1000_charge_orders_seller1(self):
        self.client.force_authenticate(user=self.user1)

        for amount in self.charge_amounts:
            ChargeOrderFactory(
                seller=self.seller1, phone_number=self.phone1, amount=amount
            )

        response = self.client.get(f"{BASE_URL}/charge-orders-list/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1000)

    def test_multiple_phones_1000_orders(self):
        self.client.force_authenticate(user=self.user1)
        initial_balance = self.seller1.balance

        phones = [self.phone1, self.phone2, self.phone3]
        orders_per_phone = 333

        for phone in phones:
            for i in range(orders_per_phone):
                amount = Decimal(str(i + 1))
                data = {
                    "seller": self.seller1.id,
                    "phone_number": phone.id,
                    "amount": str(amount),
                }
                response = self.client.post(f"{BASE_URL}/charge-orders/", data)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

                self.seller1.refresh_from_db()
                initial_balance -= amount
                self.assertEqual(self.seller1.balance, initial_balance)


def create_charge_order_worker(seller_data, phone_id, amount, base_url):
    from django.test import Client
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=seller_data["user"])

    with transaction.atomic():
        data = {
            "seller": seller_data["seller_id"],
            "phone_number": phone_id,
            "amount": str(amount),
        }

        response = client.post(f"{base_url}/charge-orders/", data)

        return {
            "status_code": response.status_code,
            "seller_id": seller_data["seller_id"],
            "phone_id": phone_id,
            "amount": str(amount),
            "response_data": response.data if response.status_code == 201 else None,
            "error": response.data if response.status_code != 201 else None,
        }


class ChargeOrderParallelAPITestCase(TransactionTestCase):
    def setUp(self):
        self.seller1 = SellerFactory(balance=Decimal("1000000.00"))
        self.seller2 = SellerFactory(balance=Decimal("3000.00"))

        self.seller1_data = {
            "user": self.seller1.user,
            "seller_id": self.seller1.id,
            "initial_balance": self.seller1.balance,
        }

        self.seller2_data = {
            "user": self.seller2.user,
            "seller_id": self.seller2.id,
            "initial_balance": self.seller2.balance,
        }

        self.phone1 = PhoneNumberFactory(phone_number="09123456789")
        self.phone2 = PhoneNumberFactory(phone_number="09123456790")
        self.phone3 = PhoneNumberFactory(phone_number="09123456791")

        self.charge_amounts = [Decimal(str(i + 1)) for i in range(1000)]
        self.base_url = BASE_URL

    def test_parallel_create_1000_charge_orders(self):
        initial_seller1_balance = self.seller1.balance
        initial_seller2_balance = self.seller2.balance

        tasks = []

        for amount in self.charge_amounts[:500]:
            tasks.append((self.seller1_data, self.phone1.id, amount, self.base_url))

        for amount in self.charge_amounts[500:800]:
            tasks.append((self.seller1_data, self.phone2.id, amount, self.base_url))

        for amount in self.charge_amounts[800:]:
            tasks.append((self.seller1_data, self.phone3.id, amount, self.base_url))

        with ProcessPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(create_charge_order_worker, *task) for task in tasks
            ]
            results = [future.result() for future in as_completed(futures)]

        successful_requests = [
            r for r in results if r["status_code"] == status.HTTP_201_CREATED
        ]
        failed_requests = [
            r for r in results if r["status_code"] != status.HTTP_201_CREATED
        ]

        self.assertEqual(len(successful_requests), 1000)
        self.assertEqual(len(failed_requests), 0)

        phone1_results = [r for r in results if r["phone_id"] == self.phone1.id]
        phone2_results = [r for r in results if r["phone_id"] == self.phone2.id]
        phone3_results = [r for r in results if r["phone_id"] == self.phone3.id]

        self.assertEqual(len(phone1_results), 500)
        self.assertEqual(len(phone2_results), 300)
        self.assertEqual(len(phone3_results), 200)

        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()

        expected_balance = initial_seller1_balance - sum(
            Decimal(r["amount"]) for r in results
        )
        # self.assertEqual(self.seller1.balance, expected_balance)
        self.assertEqual(self.seller2.balance, initial_seller2_balance)
