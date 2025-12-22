from django.template.library import Library
from django.utils.safestring import mark_safe

register = Library()


@register.simple_tag
def numadd1(num: int):
    return mark_safe('''
    <a href="www.baidu.com">123</a>
    ''')


@register.filter
def filter1(val: str):
    return val + '_1'
