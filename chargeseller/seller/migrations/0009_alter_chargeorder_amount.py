# Generated by Django 5.2.2 on 2025-06-11 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seller', '0008_remove_chargeorder_charge_orde_seller__23f157_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chargeorder',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
