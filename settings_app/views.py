
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AppSettings


@login_required
def settings_view(request):
    settings = AppSettings.get_settings()
    if request.method == 'POST':
        settings.business_name = request.POST.get('business_name', settings.business_name)
        settings.business_address = request.POST.get('business_address', '')
        settings.business_phone = request.POST.get('business_phone', '')
        settings.business_email = request.POST.get('business_email', '')
        settings.currency = request.POST.get('currency', 'GHS')
        settings.currency_symbol = request.POST.get('currency_symbol', '₵')
        settings.tax_rate = request.POST.get('tax_rate', 15)
        settings.tax_name = request.POST.get('tax_name', 'VAT')
        settings.receipt_footer = request.POST.get('receipt_footer', '')
        settings.low_stock_threshold = request.POST.get('low_stock_threshold', 10)
        settings.mtn_momo_number = request.POST.get('mtn_momo_number', '')
        settings.vodafone_cash_number = request.POST.get('vodafone_cash_number', '')
        settings.airteltigo_number = request.POST.get('airteltigo_number', '')
        settings.enable_barcode_scanner = 'enable_barcode_scanner' in request.POST
        if 'business_logo' in request.FILES:
            settings.business_logo = request.FILES['business_logo']
        settings.save()
        messages.success(request, 'Settings saved successfully.')
        return redirect('settings_app:settings')
    return render(request, 'settings_app/index.html', {'settings': settings})
