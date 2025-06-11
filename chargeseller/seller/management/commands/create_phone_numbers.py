from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from seller.models import PhoneNumber 

class Command(BaseCommand):
    help = 'Creates 100 random phone numbers in the database'

    def handle(self, *args, **options):
        for i in range(1, 101):
            phone = get_random_string(length=10, allowed_chars='09124012682')
            
            PhoneNumber.objects.create(
                phone_number=phone,
                is_active=True
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created phone number: {phone}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully created 100 phone numbers'))