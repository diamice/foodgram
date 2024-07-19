import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Командля импорта данных из json-файла в Базу Данных"""

    help = 'Help import json data into project database'

    def add_arguments(self, parser):
        parser.add_argument('filepath', help='Полный путь к файлу')

    def handle(self, *args, **options):
        filepath = options['filepath']
        try:
            with open(filepath, encoding='utf-8') as file:
                data = json.load(file)
                ingredients = [
                    Ingredient(name=item['name'],
                               measurement_unit=item['measurement_unit']
                               ) for item in data]
                Ingredient.objects.bulk_create(ingredients)
                self.stdout.write(
                    'Данные для модели Ingredient успешно импортированы'
                )
        except FileNotFoundError as err:
            self.stdout.write(f'Файл с указанным названием {filepath} '
                              f'не найден. Путь: {err}')
        except json.JSONDecodeError as err:
            self.stdout.write(self.style.ERROR(
                f'Ошибка чтения JSON файла {filepath}: {err}')
            )
        except Exception as err:
            self.stdout.write(self.style.ERROR(f'Произошла ошибка: {err}'))
