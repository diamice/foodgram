from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import UniqueConstraint

from .constants import USER_INFO_MAX_LENGTH
from .validators import validate_username


class User(AbstractUser):
    """Модель Для Пользователя"""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password')

    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
        error_messages={
            'unique': 'Пользователь с такой электронной почтой уже существует'
        }
    )

    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        max_length=USER_INFO_MAX_LENGTH,
        validators=[UnicodeUsernameValidator(), validate_username],
        unique=True,
        db_index=True,
        error_messages={
            'unique': 'Пользователь с таким юзернеймом уже существует'
        }
    )

    first_name = models.CharField(
        verbose_name='Имя',
        max_length=USER_INFO_MAX_LENGTH
    )

    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=USER_INFO_MAX_LENGTH
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользватель'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель Для Подписки на Пользователя"""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='follower'
    )

    author = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='author'
    )

    class Meta:
        verbose_name = 'Подсписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='unique_sub',
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.author}'
