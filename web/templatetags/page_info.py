from django.http import HttpRequest
from django.template import library

register = library.Library()


@register.inclusion_tag('templagetag/paginor.html')
def page_info(request: HttpRequest, page_data):
    query_dict = request.GET.copy()
    query_dict._mutable = True
    if 'page' in query_dict:
        query_dict.pop('page')
    base_query_url = '&' + query_dict.urlencode()
    return dict(page_data=page_data, base_query_url=base_query_url)
