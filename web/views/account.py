""" view about: 注册 登录 相关  """
import datetime
import random

from django.http import HttpRequest
from django.shortcuts import render, reverse, HttpResponse, redirect
from django.http.response import JsonResponse
from django_redis import get_redis_connection
from django.db.models import Q
from django.db import transaction

from web.form import account_forms
from web import models

from utils.http_response import SysHttpResponse
from utils.create_check_code import check_code
from utils.create_order_code import create_order_code
from utils import re_pat

import re

from web.form.account_forms import login_form
from io import BytesIO
from web.signals import user_register_sl

import logging

logger = logging.getLogger('django')


def register(request: HttpRequest):
    method = request.method
    if method == 'GET':
        form = account_forms.register_form()
        return render(request, 'web/account/register.html', dict(form=form))
    if method == 'POST':
        res = SysHttpResponse()
        form = account_forms.register_form(data=request.POST)
        if not form.is_valid():
            res.errors_or_data = form.errors
            return JsonResponse(res.get_dict())
        # 验证通过，新增用户，增加交易记录（绑定免费版本）
        try:
            with transaction.atomic():
                form.cleaned_data.pop('phonecode')
                form.cleaned_data.pop('confirm_password')
                # 免费价格策略
                free_policy = models.PricePolicy.objects.get(category=1)
                form.cleaned_data['price_policy_id'] = free_policy.id
                # 新建用户
                user_obj = models.UserInfo.objects.create(**form.cleaned_data)
                # 交易记录
                models.Transaction.objects.create(
                    status=2, order=create_order_code(),
                    user_id=user_obj.id, user_name=user_obj.username,
                    price_policy_id=free_policy.id, count=-1,
                    price=0, start_time=datetime.datetime.now(), end_time=None,
                    create_time=datetime.datetime.now()
                )
                # 刷新用户信息缓存, 由信号量操作
                res.status = True
                res.errors_or_data = reverse('web:login')
        except Exception as e:
            logger.error(e)
            res.errors_or_data = dict(confirm_password='系统繁忙, 请稍后重试')
        finally:
            return JsonResponse(res.get_dict())


def send_sms(request: HttpRequest):
    res = SysHttpResponse()
    phone = request.POST.get('phone', '').strip()
    # 手机号有误
    if not phone or not re.search(re_pat.PHONE_PAT, phone):
        res.errors_or_data = dict(phone='手机号格式有误')
        return JsonResponse(res.get_dict())
    # 校验手机号是否存在
    exists = models.UserInfo.objects.filter(phone=phone).exists()
    if exists:
        res.errors_or_data = dict(phone='当前手机号已存在')
        return JsonResponse(res.get_dict())
    # 手机号无误，发送验证码
    code = random.randint(1000, 9999)
    print(f'{code=}')
    try:
        # assert code % 2 == 0, '随机报错'
        get_redis_connection('default').set(phone, code, ex=5 * 60)
    except Exception as e:
        print(e)
        res.errors_or_data = dict(phone='验证码发送失败')
    else:
        res.status = True
        res.errors_or_data = code
    finally:
        return JsonResponse(res.get_dict())


def login(request: HttpRequest):
    method = request.method
    if method == 'GET':
        # 跳转登录界面
        form = login_form()
        return render(request, 'web/account/login.html', dict(form=form))
    if method == 'POST':
        form = login_form(data=request.POST)
        if not form.is_valid():
            return render(request, 'web/account/login.html', dict(form=form))
        # 数据校验-验证码
        cache_check_code = str(request.session.get('check_code', '')).upper()
        form_check_code = str(form.cleaned_data['code']).strip().upper()
        if not cache_check_code or cache_check_code != form_check_code:
            form.add_error('code', '验证码校验失败')
            return render(request, 'web/account/login.html', dict(form=form))
        # 邮箱/手机号 + 密码
        mail_phone = form.cleaned_data['mail_phone']
        password = form.cleaned_data['password']
        user_obj = models.UserInfo.objects.filter(Q(email=mail_phone) | Q(phone=mail_phone)) \
            .filter(password=password).first()
        if not user_obj:
            form.add_error('mail_phone', '用户名或密码错误')
            return render(request, 'web/account/login.html', dict(form=form))
        # 登录成功，记录session, 页面跳转
        request.session['userinfo'] = dict(userid=user_obj.id, username=user_obj.username)
        request.session.set_expiry(60 * 60 * 24 * 14)
        return redirect(reverse('web:manage_index'))


def get_checkcode(request: HttpRequest):
    img, code = check_code()
    print(f'{code=}')
    stream = BytesIO()
    img.save(stream, 'png')
    request.session['check_code'] = code  # 这也会触发所谓 滑动过期
    request.session.set_expiry(60)  # 60秒过期
    return HttpResponse(stream.getvalue())


def index(request: HttpRequest):
    return render(request, 'web/account/index.html')


def logout(request: HttpRequest):
    request.session.flush()
    return redirect(reverse('web:login'))


def get_random_username(request: HttpRequest):
    username = '1865500' + f'{random.randint(0, 9999):>04}'
    while models.UserInfo.objects.filter(username=username).count():
        username = '1865500' + f'{random.randint(0, 9999):>04}'
    print(username)
    return HttpResponse(username)
