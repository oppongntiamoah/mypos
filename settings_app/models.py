
from django.db import models
class AppSettings(models.Model):
    business_name=models.CharField(max_length=255)
    tax_rate=models.FloatField(default=0)
    currency=models.CharField(max_length=10,default='USD')
