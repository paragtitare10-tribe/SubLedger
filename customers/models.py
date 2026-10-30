from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class Customer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    name = models.CharField(max_length=160)
    email = models.EmailField()
    company_name = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('email'), name='customer_email_case_insensitive_unique'),
        ]
        ordering = ['name', 'id']

    def __str__(self):
        return self.name