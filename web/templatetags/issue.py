from django.template import library

register = library.Library()


@register.simple_tag
def str_rjust(num: int):
    if num < 100:
        num = str(num).rjust(3, '0')
    return f'#{num}'


@register.simple_tag
def first_char(val: str):
    return val[0].upper()


@register.simple_tag
def user_space(size):
    if size >= 1024 * 1024 * 1024:
        return "%.2f GB" % (size / (1024 * 1024 * 1024),)
    elif size >= 1024 * 1024:
        return "%.2f MB" % (size / (1024 * 1024),)
    elif size >= 1024:
        return "%.2f KB" % (size / 1024,)
    else:
        return "%d B" % size
