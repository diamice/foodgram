from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator

from .constants import TAG_CONSTANT, MIN_COOKING_TIME, MAX_SHOW_LENGTH, MIN_INGREDIENT_AMOUNT

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(verbose_name='Название Тега', max_length=TAG_CONSTANT, unique=True, db_index=True)
    slug = models.SlugField(verbose_name='Слаг', max_length=TAG_CONSTANT, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name[:MAX_SHOW_LENGTH]


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Название Ингредиента', max_length=128, unique=True, db_index=True)
    measurement_unit = models.CharField(verbose_name='Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_item',
            )
        ]

    def __str__(self):
        return self.name[:MAX_SHOW_LENGTH]


class Recipe(models.Model):
    """Модель Для Рецептов"""
    name = models.CharField(verbose_name='Название', max_length=256, db_index=True)
    image = models.ImageField(verbose_name='Картинка', upload_to='recipes/images/', null=True, default=None)
    text = models.TextField(verbose_name='Описание')
    author = models.ForeignKey(User, related_name='Recipe', on_delete=models.CASCADE, verbose_name='Автор')
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', related_name='recipe',
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, through='RecipeTag', related_name='recipe', verbose_name='Теги')
    cooking_time = models.IntegerField(verbose_name='Время Приготовления',
                                       validators=[MinValueValidator(MIN_COOKING_TIME,
                                                                     'Время готовки не может быть меньши минуты')])
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата Публикации')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']
        constraints = [
            UniqueConstraint(
                fields=['name', 'author'],
                name='unique_recipe',
            )
        ]

    def __str__(self):
        return self.name[:MAX_SHOW_LENGTH]


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name='Рецерт', related_name='recipe_tag')
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, verbose_name='Тег', related_name='recipe_tag')

    class Meta:
        verbose_name = 'Тег в Рецепте'
        verbose_name_plural = 'Теги в Рецепте'
        ordering = ['tag']
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_tag',
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.tag}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name='Рецерт',
                               related_name='recipe_ingredient')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.SET_NULL, null=True, verbose_name='Ингредиент',
                                   related_name='recipe_ingredient')

    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)],
    )

    class Meta:
        verbose_name = 'Ингредиент в Рецепте'
        verbose_name_plural = 'Ингредиенты в Рецепте'
        ordering = ['ingredient']
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient',
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'


class Favorite(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE, related_name='favorite')
    recipe = models.ForeignKey(Recipe, verbose_name='Рецепт', on_delete=models.CASCADE, related_name='favorite')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE, related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe, verbose_name='Рецепт', on_delete=models.CASCADE, related_name='shopping_cart')
    amount = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Список Покупок'
        verbose_name_plural = 'Списки Покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart',
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'
