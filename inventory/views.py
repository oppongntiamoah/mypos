
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum, Count, F
from django.http import HttpResponse
from django.views.decorators.http import require_POST
import csv
from pos.models import Product, Category
from settings_app.models import AppSettings
from .models import Supplier, Location, StockLevel, StockMovement, PurchaseOrder, PurchaseOrderItem


@login_required
def dashboard(request):
    settings = AppSettings.get_settings()
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(is_active=True, stock__lte=F('reorder_level'))
    out_of_stock = Product.objects.filter(is_active=True, stock=0).count()
    total_locations = Location.objects.filter(is_active=True).count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    pending_orders = PurchaseOrder.objects.filter(status__in=['draft', 'sent']).count()
    recent_movements = StockMovement.objects.select_related('product', 'location', 'created_by').order_by('-created_at')[:15]
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock': out_of_stock,
        'total_locations': total_locations,
        'total_suppliers': total_suppliers,
        'pending_orders': pending_orders,
        'low_stock_products': low_stock_products[:8],
        'recent_movements': recent_movements,
        'settings': settings,
    }
    return render(request, 'inventory/index.html', context)


@login_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    stock_filter = request.GET.get('stock', '')

    if q:
        products = products.filter(Q(name__icontains=q) | Q(barcode__icontains=q))
    if category_id:
        products = products.filter(category_id=category_id)
    if stock_filter == 'low':
        products = products.filter(stock__lte=F('reorder_level'))
    elif stock_filter == 'out':
        products = products.filter(stock=0)

    categories = Category.objects.all()
    settings = AppSettings.get_settings()
    return render(request, 'inventory/products.html', {
        'products': products,
        'categories': categories,
        'settings': settings,
        'q': q,
    })


@login_required
def product_add(request):
    categories = Category.objects.all()
    suppliers = Supplier.objects.filter(is_active=True)
    settings = AppSettings.get_settings()
    if request.method == 'POST':
        try:
            barcode = request.POST.get('barcode', '').strip() or None
            product = Product.objects.create(
                name=request.POST['name'],
                barcode=barcode,
                category_id=request.POST.get('category') or None,
                price=request.POST['price'],
                cost_price=request.POST.get('cost_price', 0),
                stock=request.POST.get('stock', 0),
                reorder_level=request.POST.get('reorder_level', 10),
                reorder_quantity=request.POST.get('reorder_quantity', 50),
                unit=request.POST.get('unit', 'pcs'),
            )
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                product.save(update_fields=['image'])
            messages.success(request, f'Product "{product.name}" added successfully.')
            return redirect('inventory:products')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'inventory/product_form.html', {
        'categories': categories,
        'suppliers': suppliers,
        'settings': settings,
        'action': 'Add',
    })


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    settings = AppSettings.get_settings()
    if request.method == 'POST':
        try:
            barcode = request.POST.get('barcode', '').strip() or None
            product.name = request.POST['name']
            product.barcode = barcode
            product.category_id = request.POST.get('category') or None
            product.price = request.POST['price']
            product.cost_price = request.POST.get('cost_price', 0)
            product.reorder_level = request.POST.get('reorder_level', 10)
            product.reorder_quantity = request.POST.get('reorder_quantity', 50)
            product.unit = request.POST.get('unit', 'pcs')
            product.is_active = 'is_active' in request.POST
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            product.save()
            messages.success(request, f'Product "{product.name}" updated.')
            return redirect('inventory:products')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'inventory/product_form.html', {
        'product': product,
        'categories': categories,
        'settings': settings,
        'action': 'Edit',
    })


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.is_active = False
        product.save(update_fields=['is_active'])
        messages.success(request, f'Product "{product.name}" deactivated.')
    return redirect('inventory:products')


@login_required
def stock_adjustment(request):
    products = Product.objects.filter(is_active=True).order_by('name')
    locations = Location.objects.filter(is_active=True)
    settings = AppSettings.get_settings()
    if request.method == 'POST':
        product_id = request.POST.get('product')
        location_id = request.POST.get('location')
        qty = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        movement_type = request.POST.get('movement_type', 'adjustment')

        product = get_object_or_404(Product, pk=product_id)
        location = get_object_or_404(Location, pk=location_id)

        with transaction.atomic():
            if movement_type in ('purchase', 'return', 'transfer_in', 'adjustment') and qty > 0:
                product.stock = max(0, product.stock + abs(qty))
            elif movement_type in ('sale', 'transfer_out') or qty < 0:
                product.stock = max(0, product.stock - abs(qty))
            product.save(update_fields=['stock'])

            stock_level, _ = StockLevel.objects.get_or_create(product=product, location=location)
            if movement_type in ('purchase', 'return', 'transfer_in', 'adjustment') and qty > 0:
                stock_level.quantity = max(0, stock_level.quantity + abs(qty))
            else:
                stock_level.quantity = max(0, stock_level.quantity - abs(qty))
            stock_level.save()

            StockMovement.objects.create(
                product=product,
                location=location,
                movement_type=movement_type,
                quantity=qty,
                notes=notes,
                created_by=request.user,
            )
        messages.success(request, 'Stock adjusted successfully.')
        return redirect('inventory:stock_movements')

    return render(request, 'inventory/stock_adjustment.html', {
        'products': products,
        'locations': locations,
        'movement_types': StockMovement.MOVEMENT_TYPES,
        'settings': settings,
    })


@login_required
def stock_movements(request):
    movements = StockMovement.objects.select_related('product', 'location', 'created_by').all()
    q = request.GET.get('q', '')
    if q:
        movements = movements.filter(Q(product__name__icontains=q) | Q(reference__icontains=q))
    settings = AppSettings.get_settings()
    return render(request, 'inventory/stock_movements.html', {
        'movements': movements[:100],
        'settings': settings,
        'q': q,
    })


@login_required
def low_stock(request):
    products = Product.objects.filter(is_active=True, stock__lte=F('reorder_level')).select_related('category').order_by('stock')
    settings = AppSettings.get_settings()
    return render(request, 'inventory/low_stock.html', {'products': products, 'settings': settings})


@login_required
def location_list(request):
    locations = Location.objects.annotate(
        product_count=Count('stock_levels')
    ).all()
    return render(request, 'inventory/locations.html', {'locations': locations})


@login_required
def location_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            is_main = 'is_main' in request.POST
            if is_main:
                Location.objects.filter(is_main=True).update(is_main=False)
            Location.objects.create(
                name=name,
                address=request.POST.get('address', ''),
                phone=request.POST.get('phone', ''),
                is_main=is_main,
            )
            messages.success(request, 'Location added.')
            return redirect('inventory:locations')
    return render(request, 'inventory/location_form.html', {'action': 'Add'})


@login_required
def location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        location.name = request.POST.get('name', location.name)
        location.address = request.POST.get('address', '')
        location.phone = request.POST.get('phone', '')
        is_main = 'is_main' in request.POST
        if is_main and not location.is_main:
            Location.objects.filter(is_main=True).update(is_main=False)
        location.is_main = is_main
        location.is_active = 'is_active' in request.POST
        location.save()
        messages.success(request, 'Location updated.')
        return redirect('inventory:locations')
    return render(request, 'inventory/location_form.html', {'location': location, 'action': 'Edit'})


@login_required
def supplier_list(request):
    suppliers = Supplier.objects.annotate(
        order_count=Count('purchase_orders')
    ).filter(is_active=True)
    return render(request, 'inventory/suppliers.html', {'suppliers': suppliers})


@login_required
def supplier_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Supplier.objects.create(
                name=name,
                contact_person=request.POST.get('contact_person', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
            )
            messages.success(request, 'Supplier added.')
            return redirect('inventory:suppliers')
    return render(request, 'inventory/supplier_form.html', {'action': 'Add'})


@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name = request.POST.get('name', supplier.name)
        supplier.contact_person = request.POST.get('contact_person', '')
        supplier.email = request.POST.get('email', '')
        supplier.phone = request.POST.get('phone', '')
        supplier.address = request.POST.get('address', '')
        supplier.is_active = 'is_active' in request.POST
        supplier.save()
        messages.success(request, 'Supplier updated.')
        return redirect('inventory:suppliers')
    return render(request, 'inventory/supplier_form.html', {'supplier': supplier, 'action': 'Edit'})


@login_required
def purchase_order_list(request):
    orders = PurchaseOrder.objects.select_related('supplier', 'location', 'created_by').all()
    return render(request, 'inventory/purchase_orders.html', {'orders': orders})


@login_required
def purchase_order_add(request):
    suppliers = Supplier.objects.filter(is_active=True)
    locations = Location.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True).order_by('name')
    settings = AppSettings.get_settings()

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        location_id = request.POST.get('location')
        notes = request.POST.get('notes', '')
        expected_date = request.POST.get('expected_date') or None
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        unit_costs = request.POST.getlist('unit_cost')

        if not supplier_id or not product_ids:
            messages.error(request, 'Supplier and at least one product are required.')
        else:
            with transaction.atomic():
                order = PurchaseOrder.objects.create(
                    supplier_id=supplier_id,
                    location_id=location_id or None,
                    notes=notes,
                    expected_date=expected_date,
                    created_by=request.user,
                )
                total = 0
                for pid, qty, cost in zip(product_ids, quantities, unit_costs):
                    if pid and int(qty) > 0:
                        item = PurchaseOrderItem.objects.create(
                            order=order,
                            product_id=pid,
                            ordered_quantity=int(qty),
                            unit_cost=cost,
                        )
                        total += item.total
                order.total = total
                order.subtotal = total
                order.save(update_fields=['total', 'subtotal'])
            messages.success(request, f'Purchase order {order.order_number} created.')
            return redirect('inventory:purchase_orders')

    return render(request, 'inventory/purchase_order_form.html', {
        'suppliers': suppliers,
        'locations': locations,
        'products': products,
        'settings': settings,
    })


@login_required
def purchase_order_detail(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    settings = AppSettings.get_settings()
    return render(request, 'inventory/purchase_order_detail.html', {'order': order, 'settings': settings})


@login_required
@require_POST
def purchase_order_receive(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if order.status in ('received', 'cancelled'):
        messages.error(request, 'Order already closed.')
        return redirect('inventory:purchase_order_detail', pk=pk)

    with transaction.atomic():
        all_received = True
        for item in order.items.select_related('product'):
            received_qty = int(request.POST.get(f'received_{item.pk}', 0))
            if received_qty > 0:
                item.received_quantity = min(received_qty, item.ordered_quantity)
                item.save(update_fields=['received_quantity'])
                item.product.stock += item.received_quantity
                item.product.save(update_fields=['stock'])
                if order.location:
                    sl, _ = StockLevel.objects.get_or_create(product=item.product, location=order.location)
                    sl.quantity += item.received_quantity
                    sl.save()
                StockMovement.objects.create(
                    product=item.product,
                    location=order.location or Location.objects.filter(is_main=True).first(),
                    movement_type='purchase',
                    quantity=item.received_quantity,
                    reference=order.order_number,
                    created_by=request.user,
                )
            if item.received_quantity < item.ordered_quantity:
                all_received = False
        order.status = 'received' if all_received else 'partial'
        order.save(update_fields=['status'])

    messages.success(request, f'Stock received for {order.order_number}.')
    return redirect('inventory:purchase_order_detail', pk=pk)


@login_required
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('products')).all()
    return render(request, 'inventory/categories.html', {'categories': categories})


@login_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Category.objects.create(name=name, description=request.POST.get('description', ''))
            messages.success(request, 'Category added.')
    return redirect('inventory:categories')


@login_required
def low_stock_count(request):
    from django.db.models import F
    count = Product.objects.filter(is_active=True, stock__lte=F('reorder_level')).count()
    return HttpResponse(f'<span class="badge badge-danger">{count}</span>' if count > 0 else '')
