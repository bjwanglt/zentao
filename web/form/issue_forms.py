from django import forms
from django.http.request import HttpRequest
from django.db.models import Q

from web import models
from web.form.FormMixin import BootstrapMixin


class IssusForm(BootstrapMixin, forms.ModelForm):

    def __init__(self, request: HttpRequest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        # self.fields.get('assign').queryset = models.UserInfo.objects.exclude(id=request.userid)
        # 指派和关注的用户需要归属当前项目
        assign_list = [('', '--------')]
        project_user_info = models.ProjectUser.objects.filter(project_id=request.proid).values_list('user_id',
                                                                                                    'user_name')
        assign_list.extend(project_user_info)
        self.fields.get('assign').choices = assign_list
        self.fields.get('attention').choices = project_user_info
        # 模块需要归属当前项目
        module_list = [('', '--------')]
        module_list.extend(
            models.Module.objects.filter(project_id=request.proid).values_list('id', 'title')
        )
        self.fields.get('module').choices = module_list
        # 父问题需要归属当前项目(修改时，排除自己)
        q = Q()
        q.connector = 'AND'
        q.children.append(('project_id', request.proid))
        if self.instance and self.instance.pk:
            q.children.append(~Q(id=self.instance.pk))
        self.fields.get('parent').queryset = models.Issues.objects.filter(q)
        # 时间格式
        self.fields.get('start_date').input_formats = ['%Y-%m-%d']
        self.fields.get('end_date').input_formats = ['%Y-%m-%d']

    def clean(self):
        cleaned_data = self.cleaned_data
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date:
            if not start_date < end_date:
                self.add_error('start_date', '开始时间需要于结束时间')
                self.add_error('end_date', '开始时间需小于结束时间')
        return cleaned_data

    class Meta:
        model = models.Issues
        fields = '__all__'
        exclude = ['project', 'creator', 'create_datetime', 'latest_update_datetime']
        widgets = {
            'assign': forms.Select(attrs={'class': "selectpicker", "data-live-search": "true"}),
            'issues_type': forms.Select(attrs={'class': "selectpicker", "data-live-search": "true"}),
            'module': forms.Select(attrs={'class': "selectpicker", "data-live-search": "true"}),
            "attention": forms.SelectMultiple(
                attrs={'class': "selectpicker", "data-live-search": "true", "data-actions-box": "true"}),
            "parent": forms.Select(attrs={'class': "selectpicker", "data-live-search": "true"}),
            "start_date": forms.DateTimeInput(format='%Y-%m-%d', attrs={'autocomplete': "off"}),
            "end_date": forms.DateTimeInput(format='%Y-%m-%d', attrs={'autocomplete': "off"})
        }


class IssueReplayForm(forms.Form):
    content = forms.CharField(max_length=200)
    parent_id = forms.IntegerField(required=False)


class ProjectInviteForm(BootstrapMixin, forms.Form):
    expire_choices = (
        (30 * 60, '30分钟'),
        (1 * 60 * 60, '1小时'),
        (5 * 60 * 60, '5小时'),
        (24 * 60 * 60, '24小时'),
    )
    expire = forms.IntegerField(required=True, label='有效期', widget=forms.Select(choices=expire_choices))
    limit_num = forms.IntegerField(required=True, label='限制数量', help_text='不填写表示无限制')
