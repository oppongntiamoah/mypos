"""
Management command: python manage.py seed_data
Creates demo data and a superuser for the POS system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pos.models import Category, Product
from inventory.models import Location, Supplier
from settings_app.models import AppSettings


class Command(BaseCommand):
    help = 'Seed demo data for the POS system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # App Settings
        settings, _ = AppSettings.objects.get_or_create(pk=1)
        settings.business_name = 'MyPOS Ghana Store'
        settings.business_address = 'Ring Road, Accra, Ghana'
        settings.business_phone = '+233 20 000 0000'
        settings.currency = 'GHS'
        settings.currency_symbol = '₵'
        settings.tax_rate = 15.00
        settings.tax_name = 'VAT'
        settings.receipt_footer = 'Thank you for shopping with us! Come again.'
        settings.save()
        self.stdout.write(self.style.SUCCESS('✓ App settings configured'))

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@mypos.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('✓ Superuser: admin / admin123'))
        else:
            self.stdout.write('  Superuser already exists')

        # Location
        location, _ = Location.objects.get_or_create(
            name='Main Store',
            defaults={'address': 'Ring Road, Accra', 'is_main': True}
        )
        self.stdout.write(self.style.SUCCESS('✓ Main location created'))

        # Supplier
        supplier, _ = Supplier.objects.get_or_create(
            name='General Supplies Ltd',
            defaults={'contact_person': 'Kwame Mensah', 'phone': '+233 24 111 2222'}
        )
        self.stdout.write(self.style.SUCCESS('✓ Supplier created'))

        # Categories
        categories = {
            'Beverages': Category.objects.get_or_create(name='Beverages')[0],
            'Snacks': Category.objects.get_or_create(name='Snacks')[0],
            'Groceries': Category.objects.get_or_create(name='Groceries')[0],
            'Personal Care': Category.objects.get_or_create(name='Personal Care')[0],
            'Household': Category.objects.get_or_create(name='Household')[0],
        }
        self.stdout.write(self.style.SUCCESS('✓ Categories created'))

        # Products
        products_data = [
            ('Coca Cola 500ml', '6001234500001', 'Beverages', 5.00, 3.50, 50, 20),
            ('Fanta Orange 500ml', '6001234500002', 'Beverages', 5.00, 3.50, 45, 20),
            ('Sprite 500ml', '6001234500003', 'Beverages', 5.00, 3.50, 40, 20),
            ('Malt Drink 330ml', '6001234500004', 'Beverages', 4.00, 2.80, 60, 24),
            ('Water 1.5L', '6001234500005', 'Beverages', 3.00, 1.80, 100, 48),
            ('Pringles Original', '6001234500006', 'Snacks', 18.00, 12.00, 30, 12),
            ('Digestive Biscuits', '6001234500007', 'Snacks', 8.00, 5.50, 25, 12),
            ('Shortbread Cookies', '6001234500008', 'Snacks', 10.00, 7.00, 20, 10),
            ('Rice 5kg', '6001234500009', 'Groceries', 55.00, 40.00, 15, 10),
            ('Cooking Oil 2L', '6001234500010', 'Groceries', 38.00, 28.00, 12, 6),
            ('Sugar 1kg', '6001234500011', 'Groceries', 10.00, 7.50, 20, 12),
            ('Tomato Paste 400g', '6001234500012', 'Groceries', 6.00, 4.00, 30, 24),
            ('Shampoo 400ml', '6001234500013', 'Personal Care', 22.00, 15.00, 10, 6),
            ('Soap (Bar)', '6001234500014', 'Personal Care', 3.50, 2.00, 50, 24),
            ('Toothpaste 100g', '6001234500015', 'Personal Care', 8.00, 5.50, 20, 12),
            ('Detergent 1kg', '6001234500016', 'Household', 15.00, 10.00, 15, 10),
            ('Bleach 750ml', '6001234500017', 'Household', 7.00, 4.50, 12, 6),
        ]

        for name, barcode, cat_name, price, cost, stock, reorder in products_data:
            Product.objects.get_or_create(
                barcode=barcode,
                defaults={
                    'name': name,
                    'category': categories[cat_name],
                    'price': price,
                    'cost_price': cost,
                    'stock': stock,
                    'reorder_level': reorder,
                    'reorder_quantity': reorder * 2,
                }
            )
        self.stdout.write(self.style.SUCCESS(f'✓ {len(products_data)} products created'))

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: admin123')
        self.stdout.write('')
        self.stdout.write('Run the server: python manage.py runserver')
        self.stdout.write('Then open: http://127.0.0.1:8000/')
        self.stdout.write('='*50)
