import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.products.models import Category, Product


class Command(BaseCommand):
    help = "Create or update the demo categories and products."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        _ = (args, options)
        seed_dir = Path(settings.BASE_DIR) / "seed_data"
        image_dir = seed_dir / "products"
        manifest_path = seed_dir / "catalog.json"

        try:
            catalog: dict[str, Any] = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(
                f"Could not read seed catalog {manifest_path}: {error}"
            ) from error

        categories = catalog.get("categories", [])
        products = catalog.get("products", [])
        if not categories or not products:
            raise CommandError("Seed catalog must define categories and products.")

        for product_data in products:
            image_path = image_dir / product_data["image"]
            if not image_path.is_file():
                raise CommandError(f"Product image does not exist: {image_path}")

        category_by_slug: dict[str, Category] = {}
        for category_data in categories:
            category, _ = Category.objects.update_or_create(
                slug=category_data["slug"],
                defaults={
                    "name": category_data["name"],
                    "description": "",
                    "parent": None,
                    "is_active": True,
                },
            )
            category_by_slug[category.slug] = category

        created_count = 0
        updated_count = 0
        image_count = 0
        for product_data in products:
            try:
                category = category_by_slug[product_data["category"]]
            except KeyError as error:
                raise CommandError(
                    f"Unknown category '{product_data['category']}' for "
                    f"product '{product_data['slug']}'."
                ) from error

            product, created = Product.objects.update_or_create(
                slug=product_data["slug"],
                defaults={
                    "name": product_data["name"],
                    "category": category,
                    "description": product_data["description"],
                    "price": product_data["price"],
                    "stock": product_data["stock"],
                    "is_active": True,
                },
            )
            created_count += int(created)
            updated_count += int(not created)

            image_name = product.image.name
            if not image_name or not product.image.storage.exists(image_name):
                image_path = image_dir / product_data["image"]
                with image_path.open("rb") as image_file:
                    product.image.save(
                        image_path.name,
                        File(image_file),
                        save=True,
                    )
                image_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalog ready: {created_count} products created, "
                f"{updated_count} updated, {image_count} images added."
            )
        )
