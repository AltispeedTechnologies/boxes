# Generated by Django 5.0.6 on 2024-06-05 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boxes', '0004_globalsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='phone_number',
            field=models.CharField(max_length=20, null=True),
        ),
    ]