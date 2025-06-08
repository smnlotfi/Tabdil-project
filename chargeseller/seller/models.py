from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal


# Create your models here.

User = get_user_model()

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
        'auth.User', 
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
       default='pending',
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