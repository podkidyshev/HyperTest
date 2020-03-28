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
                'page_size': self.page.paginator.per_page,
                'total_pages': self.page.paginator.num_pages,
                'total_items': self.page.paginator.count,
                'max_page_size': self.max_page_size,
            },
            'items': data
        })
