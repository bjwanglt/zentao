from django.template import library

register = library.Library()


@register.inclusion_tag('templagetag/wiki_cata.html')
def wiki_cata(catainfo: list):
    return dict(catainfo=catainfo)
