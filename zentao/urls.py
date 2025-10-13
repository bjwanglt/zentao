"""zentao URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.shortcuts import redirect, reverse


def to_login(request):
    return redirect(to=reverse('web:index'))


urlpatterns = [
    path('admin/', admin.site.urls),

    # 测试用  可忽略
    path('test/', include(('testapp.urls', 'test'), )),

    # 默认路径, 重定向到登录
    path('', to_login),

    # 路由分发
    path('account/', include(('web.urls', 'web'), )),

]


# def handler_500(request):
#     return JsonResponse({'code': 500, 'error': '服务器错误'}, status=500)
#
#
# handler500 = handler_500
