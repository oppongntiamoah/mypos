
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum, Count
from .models import Product, Sale, SaleItem, Customer, Category
from settings_app.models import AppSettings


def _get_cart(request):
    return request.session.get('cart', {'items': [], 'discount': '0.00'})


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _cart_totals(cart, tax_rate):
    subtotal = sum(Decimal(str(i['total'])) for i in cart['items'])
    discount = Decimal(str(cart.get('discount', '0.00')))
    taxable = subtotal - discount
    tax_amount = (taxable * Decimal(str(tax_rate)) / 100).quantize(Decimal('0.01'))
    total = taxable + tax_amount
    return subtotal, discount, tax_amount, total


@login_required
def index(request):
    settings = AppSettings.get_settings()
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).select_related('category')
    cart = _get_cart(request)
    subtotal, discount, tax_amount, total = _cart_totals(cart, settings.tax_rate)
    customers = Customer.objects.all().order_by('name')
    context = {
        'products': products,
        'categories': categories,
        'cart': cart,
        'subtotal': subtotal,
        'discount': discount,
        'tax_amount': tax_amount,
        'total': total,
        'customers': customers,
        'payment_methods': Sale.PAYMENT_METHODS,
        'settings': settings,
    }
    return render(request, 'pos/index.html', context)


@login_required
def product_search(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    products = Product.objects.filter(is_active=True)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(barcode=query))
    if category_id:
        products = products.filter(category_id=category_id)
    products = products.select_related('category')[:50]

    # If exact barcode match auto-add to cart
    if query and products.count() == 1:
        p = products.first()
        if p.barcode and p.barcode == query:
            return add_to_cart(request, p.id)

    settings = AppSettings.get_settings()
    return render(request, 'pos/partials/product_grid.html', {'products': products, 'settings': settings})


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = _get_cart(request)
    qty = int(request.POST.get('qty', 1))

    for item in cart['items']:
        if item['product_id'] == product_id:
            new_qty = item['quantity'] + qty
            if new_qty > product.stock:
                new_qty = product.stock
            item['quantity'] = new_qty
            item['total'] = str(Decimal(str(item['unit_price'])) * new_qty)
            _save_cart(request, cart)
            return _render_cart(request)

    if product.stock > 0:
        cart['items'].append({
            'product_id': product_id,
            'product_name': product.name,
            'unit_price': str(product.price),
            'quantity': min(qty, product.stock),
            'total': str(product.price * min(qty, product.stock)),
            'stock': product.stock,
        })

    _save_cart(request, cart)
    return _render_cart(request)


@login_required
@require_POST
def update_cart_item(request, product_id):
    cart = _get_cart(request)
    qty = int(request.POST.get('qty', 1))
    product = get_object_or_404(Product, pk=product_id)

    for item in cart['items']:
        if item['product_id'] == product_id:
            if qty <= 0:
                cart['items'].remove(item)
            else:
                item['quantity'] = min(qty, product.stock)
                item['total'] = str(Decimal(str(item['unit_price'])) * item['quantity'])
            break

    _save_cart(request, cart)
    return _render_cart(request)


@login_required
@require_POST
def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    cart['items'] = [i for i in cart['items'] if i['product_id'] != product_id]
    _save_cart(request, cart)
    return _render_cart(request)


@login_required
@require_POST
def clear_cart(request):
    request.session['cart'] = {'items': [], 'discount': '0.00'}
    request.session.modified = True
    return _render_cart(request)


@login_required
@require_POST
def apply_discount(request):
    cart = _get_cart(request)
    try:
        discount = Decimal(request.POST.get('discount', '0'))
        if discount < 0:
            discount = Decimal('0')
        cart['discount'] = str(discount)
    except Exception:
        cart['discount'] = '0.00'
    _save_cart(request, cart)
    return _render_cart(request)


def _render_cart(request):
    settings = AppSettings.get_settings()
    cart = _get_cart(request)
    subtotal, discount, tax_amount, total = _cart_totals(cart, settings.tax_rate)
    return render(request, 'pos/partials/cart.html', {
        'cart': cart,
        'subtotal': subtotal,
        'discount': discount,
        'tax_amount': tax_amount,
        'total': total,
        'settings': settings,
    })


@login_required
@require_POST
def checkout(request):
    cart = _get_cart(request)
    if not cart['items']:
        messages.error(request, 'Cart is empty.')
        return redirect('pos:index')

    settings = AppSettings.get_settings()
    subtotal, discount, tax_amount, total = _cart_totals(cart, settings.tax_rate)

    payment_method = request.POST.get('payment_method', 'cash')
    amount_paid = Decimal(request.POST.get('amount_paid', str(total)))
    mobile_number = request.POST.get('mobile_number', '')
    transaction_id = request.POST.get('transaction_id', '')
    customer_id = request.POST.get('customer_id', '')
    notes = request.POST.get('notes', '')

    customer = None
    if customer_id:
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            pass

    change_due = max(Decimal('0'), amount_paid - total)

    with transaction.atomic():
        sale = Sale.objects.create(
            customer=customer,
            cashier=request.user,
            subtotal=subtotal,
            tax_rate=settings.tax_rate,
            tax_amount=tax_amount,
            discount=discount,
            total=total,
            payment_method=payment_method,
            amount_paid=amount_paid,
            change_due=change_due,
            mobile_number=mobile_number,
            transaction_id=transaction_id,
            notes=notes,
        )
        for item in cart['items']:
            product = get_object_or_404(Product, pk=item['product_id'])
            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=item['product_name'],
                unit_price=Decimal(str(item['unit_price'])),
                quantity=item['quantity'],
                total=Decimal(str(item['total'])),
            )
            product.stock = max(0, product.stock - item['quantity'])
            product.save(update_fields=['stock'])

    request.session['cart'] = {'items': [], 'discount': '0.00'}
    request.session.modified = True
    messages.success(request, f'Sale #{sale.receipt_number} completed successfully!')
    return redirect('pos:receipt', sale_id=sale.pk)


@login_required
def receipt(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    settings = AppSettings.get_settings()
    return render(request, 'pos/receipt.html', {'sale': sale, 'settings': settings})


@login_required
def sales_list(request):
    sales = Sale.objects.select_related('customer', 'cashier').all()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment = request.GET.get('payment', '')

    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    if payment:
        sales = sales.filter(payment_method=payment)

    total_revenue = sales.aggregate(t=Sum('total'))['t'] or 0
    settings = AppSettings.get_settings()
    return render(request, 'pos/sales_list.html', {
        'sales': sales,
        'total_revenue': total_revenue,
        'payment_methods': Sale.PAYMENT_METHODS,
        'settings': settings,
    })


@login_required
def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    settings = AppSettings.get_settings()
    return render(request, 'pos/sale_detail.html', {'sale': sale, 'settings': settings})


@login_required
@require_POST
def void_sale(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    if sale.status == 'completed':
        with transaction.atomic():
            sale.status = 'voided'
            sale.save(update_fields=['status'])
            for item in sale.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save(update_fields=['stock'])
        messages.success(request, f'Sale #{sale.receipt_number} has been voided and stock restored.')
    return redirect('pos:sales_list')


@login_required
def customer_list(request):
    customers = Customer.objects.annotate(total_sales=Count('sales')).all()
    return render(request, 'pos/customers.html', {'customers': customers})


@login_required
def customer_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            customer = Customer.objects.create(
                name=name,
                phone=request.POST.get('phone', ''),
                email=request.POST.get('email', ''),
                address=request.POST.get('address', ''),
            )
            if request.headers.get('HX-Request'):
                return render(request, 'pos/partials/customer_option.html', {'customer': customer})
            messages.success(request, 'Customer added.')
            return redirect('pos:customers')
    return render(request, 'pos/customer_form.html', {})
