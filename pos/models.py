
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    reorder_quantity = models.IntegerField(default=50)
    unit = models.CharField(max_length=20, default='pcs')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock <= self.reorder_level

    @property
    def profit_margin(self):
        if self.cost_price and self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 0


class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card / POS Terminal'),
        ('mtn_momo', 'MTN Mobile Money'),
        ('vodafone_cash', 'Vodafone Cash'),
        ('airteltigo', 'AirtelTigo Money'),
        ('mixed', 'Mixed Payment'),
    ]
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('voided', 'Voided'),
    ]

    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mobile_number = models.CharField(max_length=20, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale #{self.receipt_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self._generate_receipt_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_receipt_number():
        now = timezone.now()
        return f"RCP-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='sale_items')
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
        self.total = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)
