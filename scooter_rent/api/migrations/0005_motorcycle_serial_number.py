# Generated by Django 5.1.3 on 2024-12-06 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_rental_total_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='motorcycle',
            name='serial_number',
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
    ]
