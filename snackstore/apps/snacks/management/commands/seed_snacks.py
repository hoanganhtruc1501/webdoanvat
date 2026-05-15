from django.core.management.base import BaseCommand
from django.utils.text import slugify

from snacks.models import Category, Snack


class Command(BaseCommand):
    help = "Create sample snack categories and products."

    def handle(self, *args, **options):
        categories = {
            "Bánh kẹo": "Các món bánh kẹo ăn vặt phổ biến.",
            "Đồ cay": "Snack cay, khô gà và các món đậm vị.",
            "Nước uống": "Nước ép, nước dừa và đồ uống giải khát.",
            "Mì ăn liền": "Mì ly, mì gói và món ăn nhanh.",
        }

        category_map = {}
        for name, description in categories.items():
            category, _ = Category.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "description": description,
                    "is_active": True,
                },
            )
            category_map[name] = category

        products = [
            {
                "title": "Bánh thảo mộc",
                "author": "Snack House",
                "category": "Bánh kẹo",
                "price": 45000,
                "discount": 15,
                "stock": 128,
                "image": "snacks/bachthao.jpg",
            },
            {
                "title": "Chân gà cay",
                "author": "Ăn Vặt Việt",
                "category": "Đồ cay",
                "price": 39000,
                "discount": 20,
                "stock": 96,
                "image": "snacks/changacay.jpg",
            },
            {
                "title": "Nước dừa Cocoxim",
                "author": "Cocoxim",
                "category": "Nước uống",
                "price": 18000,
                "discount": 5,
                "stock": 210,
                "image": "snacks/cocoxim.jpg",
            },
            {
                "title": "Mì Cung Đình",
                "author": "Cung Đình",
                "category": "Mì ăn liền",
                "price": 12000,
                "discount": 0,
                "stock": 320,
                "image": "snacks/cungdinh.jpg",
            },
            {
                "title": "Khô gà lá chanh",
                "author": "Snack House",
                "category": "Đồ cay",
                "price": 59000,
                "discount": 18,
                "stock": 142,
                "image": "snacks/galachanh.jpg",
            },
            {
                "title": "Nước ép nho",
                "author": "Fresh Drink",
                "category": "Nước uống",
                "price": 22000,
                "discount": 10,
                "stock": 180,
                "image": "snacks/nuocepnho.jpg",
            },
            {
                "title": "Snack Nhật Tâm",
                "author": "Nhật Tâm",
                "category": "Bánh kẹo",
                "price": 35000,
                "discount": 12,
                "stock": 75,
                "image": "snacks/nhattam.jpg",
            },
            {
                "title": "Khô gà 100g",
                "author": "Ăn Vặt Việt",
                "category": "Đồ cay",
                "price": 49000,
                "discount": 25,
                "stock": 118,
                "image": "snacks/ga100g.jpg",
            },
        ]

        created = 0
        updated = 0
        for product in products:
            slug = slugify(product["title"])
            _, was_created = Snack.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": product["title"],
                    "author": product["author"],
                    "description": f'{product["title"]} - sản phẩm ăn vặt chất lượng tại Snackstore.',
                    "price": product["price"],
                    "discount": product["discount"],
                    "stock": product["stock"],
                    "image": product["image"],
                    "category": category_map[product["category"]],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(category_map)} categories, created {created} products, updated {updated} products."
            )
        )
