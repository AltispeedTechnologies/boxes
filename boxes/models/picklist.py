from django.db import models
from django.core.exceptions import ValidationError

class Picklist(models.Model):
    date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def clean(self):
        if not self.date and not self.description:
            raise ValidationError("At least one of timestamp or description must be provided.")

    def save(self, *args, **kwargs):
        self.clean()
        super(Picklist, self).save(*args, **kwargs)

class PackagePicklist(models.Model):
    package = models.ForeignKey("Package", on_delete=models.RESTRICT)
    picklist = models.ForeignKey(Picklist, on_delete=models.RESTRICT)
