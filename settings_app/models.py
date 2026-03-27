
from django.db import models


class AppSettings(models.Model):
    business_name = models.CharField(max_length=200, default='MyPOS Business')
    business_address = models.TextField(blank=True, default='')
    business_phone = models.CharField(max_length=20, blank=True, default='')
    business_email = models.EmailField(blank=True, default='')
    business_logo = models.ImageField(upload_to='logo/', blank=True, null=True)
    currency = models.CharField(max_length=10, default='GHS')
    currency_symbol = models.CharField(max_length=5, default='₵')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    tax_name = models.CharField(max_length=50, default='VAT')
    receipt_footer = models.TextField(blank=True, default='Thank you for your business!')
    low_stock_threshold = models.IntegerField(default=10)
    mtn_momo_number = models.CharField(max_length=20, blank=True, default='')
    vodafone_cash_number = models.CharField(max_length=20, blank=True, default='')
    airteltigo_number = models.CharField(max_length=20, blank=True, default='')
    enable_barcode_scanner = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'

    def __str__(self):
        return self.business_name

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
