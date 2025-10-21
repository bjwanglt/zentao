import json

from django import forms
from django_celery_beat.models import CrontabSchedule
from django.db import transaction
from django.core.exceptions import ValidationError

from web.form.FormMixin import BootstrapMixin
from zentao import celery_app
from web.models import ProjectUser
import re

email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class job_form(BootstrapMixin, forms.Form):
    hours_choices = [(i, i) for i in range(0, 24)]
    minutes_choices = [(i, i) for i in range(0, 60)]

    name = forms.CharField(label='自定义名称', widget=forms.TextInput())
    task = forms.ChoiceField(label='任务类型', widget=forms.Select(attrs={'class': "select2"}))
    scheduler_hour = forms.ChoiceField(label='执行时间', widget=forms.Select(attrs={'class': "select2"}),
                                       choices=hours_choices)
    scheduler_minute = forms.ChoiceField(label='执行时间', widget=forms.Select(attrs={'class': "select2"}),
                                         choices=minutes_choices)
    args = forms.CharField(label="接收邮箱", widget=forms.Textarea(attrs=dict(placeholder='多个邮箱之间 ; 号间隔')))
    project_id = forms.ChoiceField(label='项目', widget=forms.Select(attrs={'class': "select2"}))
    crontab_id = forms.IntegerField(required=False)
    id = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        celery_app.autodiscover_tasks(force=True)
        self.__request = request
        project_id = request.resolver_match.kwargs.get('pid')
        self.fields['task'].choices = [(name, name) for name in celery_app.tasks if not name.startswith('celery.')]
        project_list = list(
            ProjectUser.objects.filter(project_id=project_id, user_role=1, user_id=request.userid).values_list(
                'project_id',
                'project_name').order_by(
                '-id'))
        self.fields['project_id'].choices = project_list

    def clean_args(self):
        email_list = [i for i in self.cleaned_data.get('args').split(';') if i]
        for email in email_list:
            if not email_pattern.fullmatch(email):
                raise ValidationError('邮箱格式有误')
        return email_list

    def clean(self):
        # 1 Schedule数据绑定
        hour = self.cleaned_data.get('scheduler_hour', None)
        minute = self.cleaned_data.get('scheduler_minute', None)
        if hour is not None and minute is not None:
            obj = None
            with transaction.atomic():
                obj = CrontabSchedule.objects.filter(hour=hour, minute=minute, day_of_week='*', day_of_month='*',
                                                     month_of_year='*',
                                                     timezone='Asia/Shanghai').select_for_update().first()
                if not obj:
                    obj = CrontabSchedule.objects.create(
                        hour=hour, minute=minute, day_of_week='*', day_of_month='*',
                        month_of_year='*', timezone='Asia/Shanghai'
                    )
            self.cleaned_data['crontab_id'] = obj.id
        # 2 定时任务参数处理  格式示例 [["2597843280@qq.com"],100]
        val_args = self.cleaned_data.get('args', None)
        val_project_id = self.__request.resolver_match.kwargs.get('pid')
        if val_args is not None and val_project_id is not None:
            self.cleaned_data['args'] = json.dumps([val_args, int(val_project_id)])
        print(self.cleaned_data)
        return self.cleaned_data
