# Create Delivery auth group for limited warehouse-floor role.

from django.db import migrations


def create_delivery_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Delivery")


def remove_delivery_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Delivery").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("boxes", "0021_pickup_day_system"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_delivery_group, remove_delivery_group),
    ]
