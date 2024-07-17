from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth import get_user_model

from recipes.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart, RecipeIngredient
from users.models import Follow
from .utils import Base64ImageField

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password', 'is_subscribed', 'avatar')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            **validated_data
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return request and request.user.is_authenticated and Follow.objects.filter(user=request.user,
                                                                                   author=obj).exists()


class UserAvatarSerializer(UserSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'avatar',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientsAddSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = [
            'id',
            'amount'
        ]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id',
        required=False
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    ingredient = IngredientSerializer(
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount', 'ingredient')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, source='recipe_ingredient')
    image = Base64ImageField(required=False, allow_null=True)
    amount = RecipeIngredientSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientsAddSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = [
            'author'
        ]

    def add_ingredients(self, ingredients, recipe):
        ingredients = [RecipeIngredient(recipe=recipe,
                                        ingredient_id=ingredient.get('id'),
                                        amount=ingredient.get('amount'))
                       for ingredient in ingredients]
        RecipeIngredient.objects.bulk_create(ingredients)

    def validate(self, attrs):
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Требуется хотя бы один ингредиент')
        ingredient_ids = [
            ingredient.get('id') for ingredient in ingredients
        ]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                'Нельзя дублировать ингредиенты'
            )
        for ingredient in ingredients:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиентов должно быть больше нуля.'
                )
        return attrs

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.add_ingredients(ingredients, instance)
        instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={'request': self.context.get('request')}).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        recipe = attrs['recipe']

        if request.method == 'POST' and Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже находится в избранном.")
        if request.method == 'DELETE' and not Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт не найден в избранном.")
        return attrs


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        recipe = attrs['recipe']
        if request.method == 'POST' and ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже есть в корзине')
        if request.method == 'DELETE' and not ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт не найден в корзине')
        return attrs


class FollowRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class UserFollowSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = FollowRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        return True


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']
        if user == author:
            raise serializers.ValidationError("Вы не можете подписаться на себя.")
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError("Вы уже подписаны на этого пользователя.")
        return data

    def to_representation(self, instance):
        context = self.context
        context['request'].user = instance.user
        serializer = UserFollowSerializer(instance.author, context=context)
        return serializer.data
