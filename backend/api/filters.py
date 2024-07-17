from django_filters import rest_framework as filters

from recipes.models import Ingredient, Tag, Recipe


class IngredientFilter(filters.FilterSet):
    """Фильтрация для модели Ingredient."""
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    """Фильтрация для модели Recipe."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorite = filters.BooleanFilter(method='filter_is_favorite')
    is_shop_cart_contain = filters.BooleanFilter(method='filter_is_shop_cart_contain')

    class Meta:
        model = Recipe
        fields = ['tags']

    def filter_is_favorite(self, queryset, item, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_is_shop_cart_contain(self, queryset, item, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

