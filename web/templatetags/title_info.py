from django.template import library
from django.http import HttpRequest
from web import models

register = library.Library()


@register.inclusion_tag('templagetag/pro_select.html')
def get_pro_info(request: HttpRequest):
    userinfo = request.session.get('userinfo')
    if userinfo:
        userid = userinfo.get('userid')
        all_pro = models.ProjectUser.objects.filter(user_id=userid).values('project_id', 'project_name')
        return dict(all_pro=all_pro)
