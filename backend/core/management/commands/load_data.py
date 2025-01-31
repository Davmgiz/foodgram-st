import csv
import os
from django.core.management.base import BaseCommand
from core.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из CSV-файла"

    def handle(self, *args, **kwargs):
        file_path = os.path.join("data", "ingredients.csv")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл {file_path} не найден!"))
            return

        with open(file_path, encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Пропускаем заголовок

            ingredients = []
            for row in reader:
                if len(row) < 2:
                    self.stdout.write(
                        self.style.WARNING(f"Пропущена строка: {row}")
                    )
                    continue
                name, measurement_unit = row
                ingredients.append(
                    Ingredient(name=name, measurement_unit=measurement_unit)
                )

            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
            self.stdout.write(
                self.style.SUCCESS("✅ Данные загружены успешно!")
            )
