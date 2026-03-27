
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('products/', views.product_list, name='products'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('stock/adjustment/', views.stock_adjustment, name='stock_adjustment'),
    path('stock/movements/', views.stock_movements, name='stock_movements'),
    path('stock/low/', views.low_stock, name='low_stock'),
    path('stock/low/count/', views.low_stock_count, name='low_stock_count'),
    path('locations/', views.location_list, name='locations'),
    path('locations/add/', views.location_add, name='location_add'),
    path('locations/<int:pk>/edit/', views.location_edit, name='location_edit'),
    path('suppliers/', views.supplier_list, name='suppliers'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('purchase-orders/', views.purchase_order_list, name='purchase_orders'),
    path('purchase-orders/add/', views.purchase_order_add, name='purchase_order_add'),
    path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/receive/', views.purchase_order_receive, name='purchase_order_receive'),
    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.category_add, name='category_add'),
]
