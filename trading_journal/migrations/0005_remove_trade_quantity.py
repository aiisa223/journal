# Generated by Django 4.2.16 on 2025-03-16 01:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trading_journal', '0004_trade_quantity_alter_trade_position_size_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trade',
            name='quantity',
        ),
    ]
