'''
customized pagination for django rest framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'utils.core.pagination.StandardResultsSetPagination'
}
'''

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'limit'
