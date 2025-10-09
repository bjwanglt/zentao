from django.template.library import Library

register = Library()


@register.inclusion_tag('templagetag/ai.html')
def ai_dialog():
    return dict()
