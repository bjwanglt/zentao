from django.urls import ResolverMatch
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from utils.http_response import SysHttpResponse
from web import models
from django.conf import settings


class check_session(MiddlewareMixin):

    def refused_request(self, request):
        if request.is_ajax():
            return SysHttpResponse(errors_or_data='鉴权失败')
        return redirect('web:index')

    def process_request(self, request: HttpRequest):
        # 放行无需校验session的请求
        if request.path_info in settings.NO_SESSION_CHECK_URLS or request.path_info.find('/admin/') != -1:
            return
            # 修复场景：用户表删除记录后，被删除用户携带cookie再次发起请求，还可以操作
        userinfo = request.session.get('userinfo')
        if userinfo:
            user_obj = models.UserInfo.objects.filter(id=userinfo['userid']).first()
            user_policy = models.PricePolicy.objects.filter(id=user_obj.price_policy_id).first()
            if not user_obj:
                # 用户已被删除，清除session, 返回报错信息或重定向
                request.session.flush()
                return self.refused_request(request)
            # 赋值request信息
            request.userid = userinfo['userid']
            request.username = userinfo['username']
            # request.policy = user_policy
        else:
            # sessioin 拦截
            return self.refused_request(request)

    def process_view(self, request: HttpRequest, callback, callback_args, callback_kwargs):
        if request.path_info.find('manage/') != -1:
            match: ResolverMatch = request.resolver_match
            pid = match.kwargs.get('pid')
            fid = request.GET.get('fid') or request.POST.get('fid')
            if pid:
                # 校验操作的项目是否归属当前用户
                pro = models.ProjectUser.objects.filter(user_id=request.userid, project_id=pid).first()
                if not pro:
                    return self.refused_request(request)
                if fid:
                    if not str(fid).isdigit():
                        return self.refused_request(request)
                    file = models.ProFile.objects.filter(id=fid).first()
                    if not file or file.project_id == pro.id:
                        return self.refused_request(request)
                    request.fileid = fid
                request.proid = pro.project_id
                request.proname = pro.project_name
                # request.project = models.Project.objects.filter(id=pro.project_id).first()
