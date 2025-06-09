from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal


# Create your models here.


class User(AbstractUser):
    is_seller = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['is_seller']),
        ]


class AbstractModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True, null=True)
    deleted_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by', null=True)


    class Meta:
        abstract = True


class Seller(AbstractModel):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='seller'
    )
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        db_table = 'sellers'
        indexes = [
            models.Index(fields=['balance']),
        ]

    def __str__(self):
        return f"{self.user.username} - Balance: {self.balance}"
    

class CreditRequest(AbstractModel):
   STATUS_CHOICES = [
       (1, 'Pending'),
       (2, 'Approved'),
       (3, 'Rejected'),
   ]
   
   seller = models.ForeignKey(
       Seller, 
       on_delete=models.CASCADE, 
       related_name='credit_requests'
   )
   amount = models.DecimalField(
       max_digits=15, 
       decimal_places=2,
       validators=[MinValueValidator(Decimal('0.01'))]
   )
   status = models.IntegerField(
       choices=STATUS_CHOICES, 
       default=1,
       db_index=True
   )
   description = models.TextField(blank=True)  
   is_processed = models.BooleanField(default=False, db_index=True)  
   processed_at = models.DateTimeField(null=True, blank=True)
   processed_by = models.ForeignKey(
       User, 
       on_delete=models.SET_NULL, 
       null=True, 
       blank=True,
       related_name='processed_credit_requests'
   )

   class Meta:
       db_table = 'credit_requests'
       ordering = ['-created_at']
       indexes = [
           models.Index(fields=['seller', 'status']),
           models.Index(fields=['status', 'is_processed']),
           models.Index(fields=['created_at']),
       ]
       
   def __str__(self):
       return f"Credit Request - {self.seller.user.username}: {self.amount} ({self.status})"
   

class PhoneNumber(AbstractModel):
    phone_number = models.CharField(
        max_length=11, 
        unique=True,
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'phone_numbers'
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.phone_number}"
    

class Transaction(AbstractModel):    
    TRANSACTION_TYPE_CHOICES = [
        (1, 'credit_increase'),
        (2, 'charge_sale'),
    ]
    
    STATUS_CHOICES = [
        (1, 'pending'),
        (2, 'completed'),
        (3, 'failed'),
        (4, 'cancelled')
    ]

    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.IntegerField(
        choices=TRANSACTION_TYPE_CHOICES,
        db_index=True
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=1,
        db_index=True
    )
    reference_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )
    credit_request = models.ForeignKey(
        CreditRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )    
    phone_number = models.ForeignKey(
        PhoneNumber,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    charge_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
    )
    balance_before = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )   
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'transaction_type']),
            models.Index(fields=['seller', 'status']),  
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Transaction {self.reference_id} - {self.seller.user.username}: {self.amount}"
    
    
    def submit_transaction_for_credit_increase(credit_request, amount):
        # Calculate balances
        balance_before = credit_request.seller.balance
        balance_after = balance_before + amount



class ChargeOrder(AbstractModel):
    
    STATUS_CHOICES = [
        (1, 'pending'),
        (2, 'processing'),
        (3, 'completed'),
        (4, 'failed'),
        (5, 'cancelled'),
    ]

    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='charge_orders'
    )
    phone_number = models.ForeignKey(
        PhoneNumber,
        on_delete=models.CASCADE,
        related_name='charge_orders'
    )
    charge_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('1000'))],
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=1,
        db_index=True
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='charge_order'
    )    
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'charge_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Order {self.id} - {self.phone_number.phone_number}: {self.charge_amount}"