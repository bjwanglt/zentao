from django import forms
from web.form.FormMixin import BootstrapMixin
from django.core.exceptions import ValidationError
from utils.encipher import md5
from utils import re_pat
from web import models
from django_redis import get_redis_connection
import re


# 注册表单
class register_form(BootstrapMixin, forms.Form):
    username = forms.CharField(label='用户名', widget=forms.TextInput())
    email = forms.CharField(label='邮箱', widget=forms.TextInput())
    phone = forms.CharField(label='手机号码', widget=forms.TextInput())
    phonecode = forms.CharField(label='验证码', widget=forms.TextInput())
    password = forms.CharField(label='密码', widget=forms.PasswordInput(render_value=True), max_length=32, min_length=8)
    confirm_password = forms.CharField(label='确认密码', widget=forms.PasswordInput(render_value=True))

    def clean_phone(self):
        phone_val = self.cleaned_data['phone']
        # 手机号格式校验
        if not re.search(re_pat.PHONE_PAT, phone_val):
            raise ValidationError('手机号格式有误')
        # 手机号重复校验
        exists = models.UserInfo.objects.filter(phone=phone_val).exists()
        if exists:
            raise ValidationError('该手机号已注册')
        return phone_val

    def clean_password(self):
        password_val = self.cleaned_data['password']
        return md5(password_val)

    def clean_phonecode(self):
        phonecode_val = self.cleaned_data['phonecode']
        phone = self.cleaned_data.get('phone', '')
        cache_phonecode = get_redis_connection('default').get(phone)
        if phone and cache_phonecode and phonecode_val == cache_phonecode.decode('utf-8'):
            return phonecode_val
        raise ValidationError('验证码失效')

    def clean(self):
        password_val = self.cleaned_data.get('password', '')
        confirm_password_val = self.cleaned_data.get('confirm_password', '')
        if password_val and confirm_password_val and password_val != md5(confirm_password_val):
            self.add_error('confirm_password', '密码不一致')
        return self.cleaned_data


# 登录表单
class login_form(BootstrapMixin, forms.Form):
    mail_phone = forms.CharField(label='邮箱或手机号', widget=forms.TextInput())
    password = forms.CharField(label='密码', widget=forms.PasswordInput())
    code = forms.CharField(label='验证码', widget=forms.TextInput())

    def clean_password(self):
        password = self.cleaned_data['password']
        return md5(password)
