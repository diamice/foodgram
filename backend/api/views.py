from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import baseconv
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import ReadOrAuthorOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          ShortRecipeSerializer, TagSerializer,
                          UserAvatarSerializer, UserFollowSerializer,
                          UserSerializer)

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
    permission_classes = (ReadOrAuthorOnly,)
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
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
        serializer = ShortRecipeSerializer(favorite.recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        serializer = FavoriteSerializer(
            data={
                'recipe': recipe.id,
                'user': user.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        favorite = Favorite.objects.get(
            user=user,
            recipe=recipe
        )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
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
        serializer = ShortRecipeSerializer(cart_item.recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated]
    )
    def delete(self, request, pk=None):
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
        cart_item = ShoppingCart.objects.get(
            user=user,
            recipe=recipe
        )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (RecipeIngredient.objects
                       .filter(recipe__shopping_cart__user=user)
                       .values('ingredient__name',
                               'ingredient__measurement_unit'
                               )
                       .annotate(amount=Sum('amount')))

        content = ['Список покупок:\n']
        for item in ingredients:
            content.append(f"{item['ingredient__name']} - {item['amount']}"
                           f" {item['ingredient__measurement_unit']}\n")

        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename="Shopping_List.txt"'
        )
        return response

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',
        url_name='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        encode_id = baseconv.base64.encode(recipe.id)
        short_link = request.build_absolute_uri(
            reverse('shortlink', kwargs={'encoded_id': encode_id})
        )
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class ShortLinkView(APIView):
    def get(self, request, encoded_id):
        if not set(encoded_id).issubset(set(baseconv.BASE64_ALPHABET)):
            return Response(
                {'error': 'Недопустимые символы в короткой ссылке.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe_id = baseconv.base64.decode(encoded_id)
        return redirect(f'/recipes/{recipe_id}/', )


class UserViewSet(djoser_views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request, id):
        user = request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(author__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = UserFollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
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

    @action(
        detail=True,
        methods=['delete']
    )
    def delete(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        user = request.user
        author = get_object_or_404(User, id=author_id)
        if not Follow.objects.filter(user=user, author=author).exists():
            return Response(
                'Подписка не найдена',
                status=status.HTTP_400_BAD_REQUEST
            )
        follow = get_object_or_404(Follow, user=user, author=author)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
