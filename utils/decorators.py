from functools import wraps

from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from utils.http_response import SysHttpResponse


def number_queryparam(param_key: list):
    """ 自定义装饰器，拦截请求中非数字类型的查询参数 """

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # 从args  kwargs 获取reuqest
            request: HttpRequest = None
            for arg in args:
                if isinstance(arg, HttpRequest):
                    request = arg
                    break
            if not request:
                for val in kwargs.values():
                    if isinstance(val, HttpRequest):
                        request = val
                        break
            # 判断param类型
            if request:
                _get = request.GET.copy()
                try:
                    for val in param_key:
                        _get[val] = int(request.GET.get(val, 0))
                    request.GET = _get
                except ValueError as e:
                    # 参数异常处理
                    if request.is_ajax():
                        return JsonResponse(SysHttpResponse(status=False, errors_or_data='参数非法').get_dict())
                    return redirect(reverse('web:index'))

            return func(*args, **kwargs)

        return inner

    return wrapper


def number_postparam(param_key: list):
    """ 自定义装饰器，拦截请求中非数字类型的表单参数 """

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # 从args  kwargs 获取reuqest
            request: HttpRequest = None
            for arg in args:
                if isinstance(arg, HttpRequest):
                    request = arg
                    break
            if not request:
                for val in kwargs.values():
                    if isinstance(val, HttpRequest):
                        request = val
                        break
            # 判断param类型
            if request:
                _post = request.POST.copy()
                try:
                    for key in param_key:
                        _post[key] = int(request.POST.get(key, 0))
                    request.POST = _post
                except ValueError as e:
                    # 参数异常处理
                    if request.is_ajax():
                        return JsonResponse(SysHttpResponse(status=False, errors_or_data='参数非法').get_dict())
                    return redirect(reverse('web:index'))
            return func(*args, **kwargs)

        return inner

    return wrapper
