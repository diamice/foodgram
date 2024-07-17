from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, IngredientViewSet, TagViewSet, UserViewSet

router_v1 = DefaultRouter()
router_v1.register(r'recipes', RecipeViewSet, basename='recipe')
router_v1.register(r'tags', TagViewSet, basename='tag')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredient')
router_v1.register(r'users/me/avatar', UserViewSet, basename='avatar')
router_v1.register(r'users', UserViewSet, basename='user')


urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls))
]