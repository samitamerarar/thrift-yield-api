# Generated by Django 3.2.23 on 2024-01-14 22:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_investment'),
    ]

    operations = [
        migrations.AddField(
            model_name='investment',
            name='link',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
