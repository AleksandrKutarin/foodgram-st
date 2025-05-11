import json
from django.core.management.base import BaseCommand
from api.models import Ingredient


class Command(BaseCommand):
    help = '''Deletes all existing ingredients and loads fresh
     ones from ingredients.json, stripping whitespace.'''

    def handle(self, *args, **options):
        try:
            deleted_count, _ = Ingredient.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'''Successfully deleted
             {deleted_count} existing ingredients.'''))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR
                (f'Error deleting ingredients: {e}')
            )

        file_path = 'data_for_management/ingredients.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR
                (f'File not found: {file_path}')
            )
            return
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR
                (f'Error decoding JSON from {file_path}')
            )
            return

        ingredients_to_create = []
        for item in ingredients_data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')
            if name and measurement_unit:
                ingredients_to_create.append(
                    Ingredient(
                        name=name.strip(),
                        measurement_unit=measurement_unit.strip()
                    )
                )
            else:
                self.stdout.write(self.style.WARNING(
                    f'''Skipping item due to missing
                     name or measurement_unit: {item}'''
                ))

        if ingredients_to_create:
            try:
                Ingredient.objects.bulk_create(
                    ingredients_to_create,
                    ignore_conflicts=True
                )
                self.stdout.write(self.style.SUCCESS(
                    f'''Successfully loaded {len(ingredients_to_create)}
                     ingredients.'''
                ))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR
                    (f'Error saving ingredients: {e}')
                )
        else:
            self.stdout.write(
                self.style.WARNING
                ('No ingredients to load.')
            )
