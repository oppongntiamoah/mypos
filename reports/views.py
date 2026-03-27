
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
import json
from pos.models import Sale, SaleItem, Product, Category
from settings_app.models import AppSettings


@login_required
def dashboard(request):
    settings = AppSettings.get_settings()
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    today_sales = Sale.objects.filter(created_at__date=today, status='completed')
    today_revenue = today_sales.aggregate(t=Sum('total'))['t'] or 0
    today_count = today_sales.count()

    week_sales = Sale.objects.filter(created_at__date__gte=week_ago, status='completed')
    week_revenue = week_sales.aggregate(t=Sum('total'))['t'] or 0

    month_sales = Sale.objects.filter(created_at__date__gte=month_ago, status='completed')
    month_revenue = month_sales.aggregate(t=Sum('total'))['t'] or 0
    month_count = month_sales.count()

    all_sales = Sale.objects.filter(status='completed')
    total_revenue = all_sales.aggregate(t=Sum('total'))['t'] or 0

    # Sales by payment method this month
    payment_breakdown = month_sales.values('payment_method').annotate(
        count=Count('id'), total=Sum('total')
    ).order_by('-total')

    # Daily sales for last 7 days
    daily_sales = Sale.objects.filter(
        created_at__date__gte=week_ago, status='completed'
    ).annotate(day=TruncDate('created_at')).values('day').annotate(
        total=Sum('total'), count=Count('id')
    ).order_by('day')

    daily_labels = []
    daily_data = []
    for entry in daily_sales:
        daily_labels.append(entry['day'].strftime('%b %d'))
        daily_data.append(float(entry['total']))

    # Top selling products this month
    top_products = SaleItem.objects.filter(
        sale__created_at__date__gte=month_ago, sale__status='completed'
    ).values('product_name').annotate(
        qty=Sum('quantity'), revenue=Sum('total')
    ).order_by('-qty')[:10]

    # Recent sales
    recent_sales = Sale.objects.select_related('customer', 'cashier').filter(
        status='completed'
    ).order_by('-created_at')[:10]

    context = {
        'today_revenue': today_revenue,
        'today_count': today_count,
        'week_revenue': week_revenue,
        'month_revenue': month_revenue,
        'month_count': month_count,
        'total_revenue': total_revenue,
        'payment_breakdown': payment_breakdown,
        'daily_labels': json.dumps(daily_labels),
        'daily_data': json.dumps(daily_data),
        'top_products': top_products,
        'recent_sales': recent_sales,
        'settings': settings,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def sales_report(request):
    settings = AppSettings.get_settings()
    sales = Sale.objects.select_related('customer', 'cashier').filter(status='completed')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment = request.GET.get('payment', '')
    cashier_id = request.GET.get('cashier', '')

    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    if payment:
        sales = sales.filter(payment_method=payment)
    if cashier_id:
        sales = sales.filter(cashier_id=cashier_id)

    totals = sales.aggregate(
        revenue=Sum('total'),
        tax=Sum('tax_amount'),
        discount=Sum('discount'),
        count=Count('id'),
    )

    from django.contrib.auth.models import User
    cashiers = User.objects.filter(sales__isnull=False).distinct()

    context = {
        'sales': sales[:200],
        'totals': totals,
        'payment_methods': Sale.PAYMENT_METHODS,
        'cashiers': cashiers,
        'settings': settings,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'reports/sales_report.html', context)


@login_required
def inventory_report(request):
    settings = AppSettings.get_settings()
    from django.db.models import F
    products = Product.objects.select_related('category').filter(is_active=True).annotate(
        stock_value=F('stock') * F('cost_price'),
        retail_value=F('stock') * F('price'),
    ).order_by('category__name', 'name')

    total_stock_value = sum(p.stock_value for p in products if p.stock_value)
    total_retail_value = sum(p.retail_value for p in products if p.retail_value)

    categories = Category.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock'),
    ).all()

    context = {
        'products': products,
        'total_stock_value': total_stock_value,
        'total_retail_value': total_retail_value,
        'categories': categories,
        'settings': settings,
    }
    return render(request, 'reports/inventory_report.html', context)
