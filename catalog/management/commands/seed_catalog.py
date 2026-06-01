import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
import requests

from users.models import User
from catalog.models import (
    Category, Seller, Product, ProductImage,
    AttributeKey, ProductVariant, VariantAttribute,
    Warehouse, Inventory,
)


CATEGORIES = [
    {'name': 'Electronics', 'slug': 'electronics', 'display_order': 1, 'children': [
        {'name': 'Mobile Phones', 'slug': 'mobile-phones', 'display_order': 1},
        {'name': 'Laptops', 'slug': 'laptops', 'display_order': 2},
        {'name': 'Headphones', 'slug': 'headphones', 'display_order': 3},
        {'name': 'Cameras', 'slug': 'cameras', 'display_order': 4},
    ]},
    {'name': 'Clothing', 'slug': 'clothing', 'display_order': 2, 'children': [
        {'name': 'Men', 'slug': 'men', 'display_order': 1},
        {'name': 'Women', 'slug': 'women', 'display_order': 2},
        {'name': 'Kids', 'slug': 'kids', 'display_order': 3},
    ]},
    {'name': 'Home & Garden', 'slug': 'home-garden', 'display_order': 3, 'children': [
        {'name': 'Furniture', 'slug': 'furniture', 'display_order': 1},
        {'name': 'Kitchen', 'slug': 'kitchen', 'display_order': 2},
        {'name': 'Lighting', 'slug': 'lighting', 'display_order': 3},
    ]},
]

PRODUCTS = [
    {
        'name': 'Samsung Galaxy S24 Ultra',
        'slug': 'samsung-galaxy-s24-ultra',
        'description': 'Flagship smartphone with S Pen and AI features. 6.8-inch Dynamic AMOLED display, 200MP camera, Snapdragon 8 Gen 3 processor.',
        'brand': 'Samsung',
        'category_slug': 'mobile-phones',
        'variants': [
            {'sku': 'SAM-S24U-256-BLK', 'price': Decimal('1299.99'), 'attributes': {'color': 'black', 'storage': '256gb'}},
            {'sku': 'SAM-S24U-512-BLK', 'price': Decimal('1419.99'), 'attributes': {'color': 'black', 'storage': '512gb'}},
            {'sku': 'SAM-S24U-256-TIT', 'price': Decimal('1299.99'), 'attributes': {'color': 'titanium', 'storage': '256gb'}},
        ],
        'inventory': 150,
    },
    {
        'name': 'iPhone 15 Pro Max',
        'slug': 'iphone-15-pro-max',
        'description': 'Apple latest flagship with A17 Pro chip, titanium design, and 48MP camera system. USB-C, Action Button.',
        'brand': 'Apple',
        'category_slug': 'mobile-phones',
        'variants': [
            {'sku': 'APL-15PM-256-BLK', 'price': Decimal('1199.00'), 'attributes': {'color': 'black', 'storage': '256gb'}},
            {'sku': 'APL-15PM-512-BLK', 'price': Decimal('1399.00'), 'attributes': {'color': 'black', 'storage': '512gb'}},
            {'sku': 'APL-15PM-1TB-BLK', 'price': Decimal('1599.00'), 'attributes': {'color': 'black', 'storage': '1tb'}},
        ],
        'inventory': 200,
    },
    {
        'name': 'MacBook Pro 14-inch M3 Pro',
        'slug': 'macbook-pro-14-m3-pro',
        'description': 'Professional laptop with M3 Pro chip, 18GB unified memory, Liquid Retina XDR display, up to 18 hours battery.',
        'brand': 'Apple',
        'category_slug': 'laptops',
        'variants': [
            {'sku': 'APL-MBP14-M3P-18G', 'price': Decimal('1999.00'), 'attributes': {'memory': '18gb', 'color': 'space-black'}},
            {'sku': 'APL-MBP14-M3P-36G', 'price': Decimal('2399.00'), 'attributes': {'memory': '36gb', 'color': 'space-black'}},
        ],
        'inventory': 75,
    },
    {
        'name': 'Dell XPS 15',
        'slug': 'dell-xps-15',
        'description': 'Premium ultrabook with 13th Gen Intel Core i7, 16GB RAM, 512GB SSD, 15.6-inch OLED display.',
        'brand': 'Dell',
        'category_slug': 'laptops',
        'variants': [
            {'sku': 'DEL-XPS15-I7-16', 'price': Decimal('1499.99'), 'attributes': {'memory': '16gb', 'storage': '512gb'}},
            {'sku': 'DEL-XPS15-I7-32', 'price': Decimal('1799.99'), 'attributes': {'memory': '32gb', 'storage': '1tb'}},
        ],
        'inventory': 60,
    },
    {
        'name': 'Sony WH-1000XM5',
        'slug': 'sony-wh-1000xm5',
        'description': 'Industry-leading noise cancelling headphones. 30-hour battery, multipoint connection, speak-to-chat.',
        'brand': 'Sony',
        'category_slug': 'headphones',
        'variants': [
            {'sku': 'SNY-WH1000-BLK', 'price': Decimal('349.99'), 'attributes': {'color': 'black'}},
            {'sku': 'SNY-WH1000-SLV', 'price': Decimal('349.99'), 'attributes': {'color': 'silver'}},
        ],
        'inventory': 300,
    },
    {
        'name': 'AirPods Pro 2',
        'slug': 'airpods-pro-2',
        'description': 'Apple wireless earbuds with adaptive audio, personalized spatial audio, USB-C MagSafe charging case.',
        'brand': 'Apple',
        'category_slug': 'headphones',
        'variants': [
            {'sku': 'APL-APP2-WHT', 'price': Decimal('249.00'), 'attributes': {'color': 'white'}},
        ],
        'inventory': 500,
    },
    {
        'name': 'Canon EOS R6 Mark II',
        'slug': 'canon-eos-r6-ii',
        'description': 'Full-frame mirrorless camera, 24.2MP sensor, 40fps continuous shooting, 4K 60p video, in-body stabilization.',
        'brand': 'Canon',
        'category_slug': 'cameras',
        'variants': [
            {'sku': 'CAN-R6II-BODY', 'price': Decimal('2499.00'), 'attributes': {'type': 'body-only'}},
            {'sku': 'CAN-R6II-24105', 'price': Decimal('3599.00'), 'attributes': {'type': 'with-24-105mm'}},
        ],
        'inventory': 30,
    },
    {
        'name': 'Levi\'s 501 Original Fit Jeans',
        'slug': 'levis-501-original',
        'description': 'The original blue jean since 1873. Straight fit through the thigh, iconic button fly, 100% cotton denim.',
        'brand': 'Levi\'s',
        'category_slug': 'men',
        'variants': [
            {'sku': 'LEV-501-28-BLU', 'price': Decimal('69.50'), 'attributes': {'size': '28', 'color': 'blue'}},
            {'sku': 'LEV-501-30-BLU', 'price': Decimal('69.50'), 'attributes': {'size': '30', 'color': 'blue'}},
            {'sku': 'LEV-501-32-BLU', 'price': Decimal('69.50'), 'attributes': {'size': '32', 'color': 'blue'}},
            {'sku': 'LEV-501-34-BLU', 'price': Decimal('69.50'), 'attributes': {'size': '34', 'color': 'blue'}},
        ],
        'inventory': 400,
    },
    {
        'name': 'Nike Air Max 270',
        'slug': 'nike-air-max-270',
        'description': 'Lifestyle sneakers with the biggest Nike Air unit yet. Lightweight mesh upper, Max Air unit for cushioning.',
        'brand': 'Nike',
        'category_slug': 'men',
        'variants': [
            {'sku': 'NIK-AM270-9-BLK', 'price': Decimal('159.99'), 'attributes': {'size': '9', 'color': 'black'}},
            {'sku': 'NIK-AM270-10-BLK', 'price': Decimal('159.99'), 'attributes': {'size': '10', 'color': 'black'}},
            {'sku': 'NIK-AM270-11-WHT', 'price': Decimal('159.99'), 'attributes': {'size': '11', 'color': 'white'}},
        ],
        'inventory': 250,
    },
    {
        'name': 'Zara Floral Summer Dress',
        'slug': 'zara-floral-summer-dress',
        'description': 'Lightweight floral print dress with V-neckline, short puff sleeves, and A-line silhouette. Perfect for summer.',
        'brand': 'Zara',
        'category_slug': 'women',
        'variants': [
            {'sku': 'ZAR-FSD-S-BLU', 'price': Decimal('49.90'), 'attributes': {'size': 's', 'color': 'blue'}},
            {'sku': 'ZAR-FSD-M-BLU', 'price': Decimal('49.90'), 'attributes': {'size': 'm', 'color': 'blue'}},
            {'sku': 'ZAR-FSD-L-BLU', 'price': Decimal('49.90'), 'attributes': {'size': 'l', 'color': 'blue'}},
        ],
        'inventory': 180,
    },
    {
        'name': 'IKEA MALM Bed Frame',
        'slug': 'ikea-malm-bed-frame',
        'description': 'Clean lines with a timeless expression. Adjustable bed sides, solid pine with stain finish. Fits standard mattresses.',
        'brand': 'IKEA',
        'category_slug': 'furniture',
        'variants': [
            {'sku': 'IKEA-MALM-FULL', 'price': Decimal('249.00'), 'attributes': {'size': 'full'}},
            {'sku': 'IKEA-MALM-QUEEN', 'price': Decimal('299.00'), 'attributes': {'size': 'queen'}},
            {'sku': 'IKEA-MALM-KING', 'price': Decimal('399.00'), 'attributes': {'size': 'king'}},
        ],
        'inventory': 50,
    },
    {
        'name': 'Philips Hue Starter Kit',
        'slug': 'philips-hue-starter-kit',
        'description': 'Smart lighting starter kit with 3 color-capable A19 bulbs and Hue Bridge. Voice control with Alexa and Google.',
        'brand': 'Philips',
        'category_slug': 'lighting',
        'variants': [
            {'sku': 'PHI-HUE-3BLB-WHT', 'price': Decimal('179.99'), 'attributes': {'bulbs': '3', 'type': 'color'}},
        ],
        'inventory': 120,
    },
]

WAREHOUSES = [
    {'name': 'Dhaka Central Warehouse', 'address': '45 Industrial Area', 'city': 'Dhaka', 'country': 'Bangladesh'},
    {'name': 'Chittagong Port Warehouse', 'address': '12 Port Road', 'city': 'Chittagong', 'country': 'Bangladesh'},
]


class Command(BaseCommand):
    help = 'Seed the database with sample catalog data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing catalog data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Inventory.objects.all().delete()
            ProductVariant.objects.all().delete()
            ProductImage.objects.all().delete()
            Product.objects.all().delete()
            Seller.objects.all().delete()
            Category.objects.all().delete()
            Warehouse.objects.all().delete()
            AttributeKey.objects.all().delete()

        self.stdout.write('Creating seller user...')
        user, _ = User.objects.get_or_create(
            email='seller@example.com',
            defaults={
                'username': 'seller',
                'is_staff': True,
            }
        )
        if not hasattr(user, 'seller_profile'):
            user.set_password('seller1234')
            user.save()
            Seller.objects.create(user=user, store_name='Nazmul E-Commerce Store')
        seller = user.seller_profile

        self.stdout.write('Creating categories...')
        category_map = {}
        for cat_data in CATEGORIES:
            parent, _ = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'display_order': cat_data['display_order'],
                    'is_active': True,
                }
            )
            category_map[cat_data['slug']] = parent
            for child_data in cat_data.get('children', []):
                child, _ = Category.objects.get_or_create(
                    slug=child_data['slug'],
                    defaults={
                        'name': child_data['name'],
                        'parent': parent,
                        'display_order': child_data['display_order'],
                        'is_active': True,
                    }
                )
                category_map[child_data['slug']] = child

        self.stdout.write('Creating warehouses...')
        warehouse_objs = []
        for wh_data in WAREHOUSES:
            wh, _ = Warehouse.objects.get_or_create(
                name=wh_data['name'],
                defaults=wh_data
            )
            warehouse_objs.append(wh)

        self.stdout.write('Creating products with variants and inventory...')
        for prod_data in PRODUCTS:
            category = category_map.get(prod_data['category_slug'])
            if not category:
                self.stderr.write(f"Category {prod_data['category_slug']} not found, skipping {prod_data['name']}")
                continue

            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults={
                    'seller': seller,
                    'category': category,
                    'name': prod_data['name'],
                    'description': prod_data['description'],
                    'brand': prod_data.get('brand', ''),
                    'is_active': True,
                }
            )

            if created:
                placeholder_url = f"https://picsum.photos/seed/{prod_data['slug']}/800/800"
                try:
                    response = requests.get(placeholder_url, timeout=10)
                    if response.status_code == 200:
                        ProductImage.objects.create(
                            product=product,
                            image=ContentFile(response.content, name=f"{prod_data['slug']}.jpg"),
                            is_primary=True,
                            order=0,
                        )
                except Exception:
                    pass

                for var_data in prod_data.get('variants', []):
                    normalized_attrs = {k.strip().lower(): v.strip().lower() for k, v in var_data.get('attributes', {}).items()}
                    import hashlib
                    if normalized_attrs:
                        pairs = sorted(normalized_attrs.items())
                        raw = "&".join(f"{k}={v}" for k, v in pairs)
                        attr_hash = hashlib.sha256(raw.encode()).hexdigest()
                    else:
                        attr_hash = hashlib.sha256(b'__empty__').hexdigest()

                    variant = ProductVariant.objects.create(
                        product=product,
                        sku=var_data['sku'],
                        price=var_data['price'],
                        attribute_hash=attr_hash,
                    )

                    for key_name, value in normalized_attrs.items():
                        key_obj, _ = AttributeKey.objects.get_or_create(name=key_name)
                        VariantAttribute.objects.create(
                            variant=variant,
                            key=key_obj,
                            value=value,
                        )

                    wh = random.choice(warehouse_objs)
                    Inventory.objects.get_or_create(
                        variant=variant,
                        warehouse=wh,
                        defaults={'quantity': prod_data.get('inventory', 0) // len(prod_data.get('variants', [1]))},
                    )

            self.stdout.write(f"  - {prod_data['name']}")

        total_products = Product.objects.count()
        total_variants = ProductVariant.objects.count()
        total_inventory = Inventory.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created {total_products} products, '
            f'{total_variants} variants, {total_inventory} inventory records.'
        ))
