from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class Pagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 40

    def get_paginated_response(self, data):
        return Response({
            '_metadata': {
                'page': self.page.number,
                'per_page': self.page.paginator.per_page,
                'total_pages': self.page.paginator.count,
            },
            'items': data
        })
