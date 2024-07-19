from django.contrib import admin

from .models import Tag, Recipe, Ingredient, Favorite, ShoppingCart


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    empty_value_display = 'Нет Информации'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = 'Нет Информации'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_counter')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags__name',)
    empty_value_display = 'Нет Информации'

    @admin.display(
        description='Общее число добавлений этого рецепта в избранное'
    )
    def favorite_counter(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('recipe__name', 'author__username')
    empty_value_display = 'Нет Информации'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__name', 'recipe__name')
    empty_value_display = 'Нет Информации'
