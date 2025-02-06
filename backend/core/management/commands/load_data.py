import json
import os
from django.core.management.base import BaseCommand
from core.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из JSON-фикстуры"

    def handle(self, *args, **kwargs):
        file_path = os.path.join("data", "ingredients.json")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл {file_path} не найден!"))
            return

        with open(file_path, encoding="utf-8") as file:
            data = json.load(file)

        created_objects = Ingredient.objects.bulk_create(
            [Ingredient(**row) for row in data], ignore_conflicts=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                (f"Данные загружены успешно! Добавлено "
                 f"{len(created_objects)} записей.")
            )
        )
