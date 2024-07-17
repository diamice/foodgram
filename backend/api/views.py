from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from djoser import views as djoser_views

from .serializers import (TagSerializer, IngredientSerializer, RecipeSerializer, UserSerializer, UserFollowSerializer,
                          FollowSerializer, ShoppingCartSerializer, RecipeCreateSerializer, FavoriteSerializer,
                          UserAvatarSerializer)
from .pagination import CustomPagination
from .filters import IngredientFilter, RecipeFilter
from .permissions import ReadOrAuthorOnly
from recipes.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart, RecipeIngredient
from users.models import Follow

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        serializer = FavoriteSerializer(
            data={
                'recipe': recipe.id,
                'user': user.id
            },
            context={
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        favorite, created = Favorite.objects.get_or_create(
            user=user,
            recipe=recipe
        )
        serializer = RecipeSerializer(favorite.recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        try:
            favorite = Favorite.objects.get(
                user=user,
                recipe=recipe
            )
        except Favorite.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        serializer = ShoppingCartSerializer(
            data={
                'recipe': recipe.id,
                'user': user.id
            },
            context={
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        cart_item = ShoppingCart.objects.create(
            user=user,
            recipe=recipe
        )
        serializer = RecipeSerializer(
            cart_item.recipe
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'])
    def delete(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        try:
            cart_item = ShoppingCart.objects.get(
                user=user,
                recipe=recipe
            )
        except ShoppingCart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(request):
        queryset = Recipe.objects.filter(shopping_cart__user=request.user)
        ingredients = (queryset.values_list(
            'recipe_ingredients__ingredient__name',
            'recipe_ingredients__ingredient__measurement_unit')
                       .annotate(amount=Sum('recipe_ingredients__amount')))
        content = ['Список покупок:\n']
        for ingredient in ingredients:
            ingredient, amount, measurement_unit = ingredient
            content.append(f'{ingredient} - {measurement_unit} {amount}\n')
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="Shopping_List.txt"'
        return response


class UserViewSet(djoser_views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=['put', 'delete'], permission_classes=[IsAuthenticated])
    def avatar(self, request, id):
        user = request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(author__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = UserFollowSerializer(pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        user = request.user
        author = get_object_or_404(User, id=author_id)
        serializer = FollowSerializer(
            data={
                'user': user.id,
                'author': author.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def delete(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        user = request.user
        author = get_object_or_404(User, id=author_id)
        if not Follow.objects.filter(follower=user, author=author).exists():
            return Response(
                'Подписка не найдена',
                status=status.HTTP_400_BAD_REQUEST
            )
        follow = get_object_or_404(Follow, user=user, author=author)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
