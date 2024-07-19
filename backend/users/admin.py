from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'password')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = 'Нет Информации'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user',)
