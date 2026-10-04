from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """
    Пагинация по номеру страницы.

    Размер страницы можно менять через параметр limit.
    """

    page_size_query_param = 'limit'
