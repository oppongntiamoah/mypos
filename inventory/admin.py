
from django.contrib import admin
from .models import Supplier, Location, StockLevel, StockMovement, PurchaseOrder, PurchaseOrderItem


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active']
    search_fields = ['name', 'contact_person', 'phone']
    list_filter = ['is_active']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'phone', 'is_main', 'is_active']
    list_filter = ['is_main', 'is_active']


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'quantity']
    list_filter = ['location']
    search_fields = ['product__name']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'movement_type', 'quantity', 'reference', 'created_by', 'created_at']
    list_filter = ['movement_type', 'location', 'created_at']
    search_fields = ['product__name', 'reference']


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'location', 'status', 'total', 'created_at']
    list_filter = ['status', 'supplier']
    search_fields = ['order_number', 'supplier__name']
    readonly_fields = ['order_number', 'created_at']
    inlines = [PurchaseOrderItemInline]
