from django.template import library

register = library.Library()


@register.simple_tag
def handle_email_args(val_email):
    print(f'{val_email=}')
    print(f'{type(val_email)=}')
    return val_email
