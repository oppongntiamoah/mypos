
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales'),
    path('inventory/', views.inventory_report, name='inventory'),
]
