
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from pos.models import Product


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_locations')
    is_main = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', 'name']

    def __str__(self):
        return self.name


class StockLevel(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_levels')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='stock_levels')
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ['product', 'location']

    def __str__(self):
        return f"{self.product.name} @ {self.location.name}: {self.quantity}"

    @property
    def is_low(self):
        return self.quantity <= self.product.reorder_level


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('purchase', 'Purchase / Received'),
        ('sale', 'Sale'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('adjustment', 'Stock Adjustment'),
        ('return', 'Return / Refund'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        direction = '+' if self.quantity > 0 else ''
        return f"{self.movement_type} {direction}{self.quantity} × {self.product.name}"


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    expected_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PO #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        now = timezone.now()
        return f"PO-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


class PurchaseOrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='po_items')
    ordered_quantity = models.IntegerField()
    received_quantity = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} x{self.ordered_quantity}"

    def save(self, *args, **kwargs):
        self.total = self.unit_cost * self.ordered_quantity
        super().save(*args, **kwargs)
