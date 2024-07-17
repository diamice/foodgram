from rest_framework import pagination

from .constants import PAGE_SIZE


class CustomPagination(pagination.PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
