
from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.product_search, name='product_search'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/discount/', views.apply_discount, name='apply_discount'),
    path('checkout/', views.checkout, name='checkout'),
    path('receipt/<int:sale_id>/', views.receipt, name='receipt'),
    path('sales/', views.sales_list, name='sales_list'),
    path('sales/<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:sale_id>/void/', views.void_sale, name='void_sale'),
    path('customers/', views.customer_list, name='customers'),
    path('customers/add/', views.customer_add, name='customer_add'),
]
