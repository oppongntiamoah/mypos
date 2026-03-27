
from django.contrib import admin
from .models import Category, Product, Customer, Sale, SaleItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'barcode', 'category', 'price', 'cost_price', 'stock', 'reorder_level', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'barcode']
    list_editable = ['price', 'stock', 'is_active']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email']


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['product_name', 'unit_price', 'quantity', 'total']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'customer', 'cashier', 'total', 'payment_method', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['receipt_number', 'customer__name', 'cashier__username']
    readonly_fields = ['receipt_number', 'created_at']
    inlines = [SaleItemInline]
