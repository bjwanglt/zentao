from django import forms
from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from django.db.models import Q

from web import models
from web.form.FormMixin import BootstrapMixin
from web.models import ProjectVersion, ProjectDemand


class SkipValidModelChoiceField(forms.models.ModelChoiceField):

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or 'pk'
            if isinstance(value, ProjectDemand):
                value = getattr(value, key)
            value = ProjectDemand.objects.get(**{key: value})
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
        return value


class IssusForm(BootstrapMixin, forms.ModelForm):
    def __init__(self, request: HttpRequest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        project_id = request.resolver_match.kwargs.get('pid')
        # 指派和关注的用户需要归属当前项目
        assign_list = [('', '--------')]
        if self.instance and self.instance.pk:
            # 数据修改
            project_user_info = models.ProjectUser.objects \
                .filter(user_id=self.instance.assign_id, project_id=project_id) \
                .exclude(user_id=self.instance.creator_id) \
                .values_list('user_id', 'user_name')
        else:
            # 数据新建
            project_user_info = models.ProjectUser.objects\
                .filter(project_id=project_id)\
                .exclude(user_id=request.userid).values_list('user_id', 'user_name')
        assign_list.extend(project_user_info)
        self.fields.get('assign').choices = assign_list
        # 获取项目下的版本
        self.fields.get('version').queryset = ProjectVersion.objects.filter(project_id=project_id)

        self.fields.get('demand').queryset = ProjectDemand.objects.none()
        if self.instance.version_id:
            self.fields.get('demand').queryset = ProjectDemand.objects.filter(version_id=self.instance.version_id)
        if self.data.get('demand', ''):
            self.fields.get('demand').queryset = ProjectDemand.objects.filter(version__project_id=project_id)

        # 时间格式
        self.fields.get('start_date').input_formats = ['%Y-%m-%d']
        self.fields.get('end_date').input_formats = ['%Y-%m-%d']
        print(f'{type(self.fields.get("version"))=}')

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
            'mode': forms.Select(attrs={'class': "select2"}),
            'priority': forms.Select(attrs={'class': "select2"}),
            'status': forms.Select(attrs={'style': 'display:none'}),
            'assign': forms.Select(attrs={'class': "select2"}),
            'issues_type': forms.Select(attrs={'class': "select2"}),
            'module': forms.Select(attrs={'class': "select2"}),
            "start_date": forms.DateTimeInput(format='%Y-%m-%d', attrs={'autocomplete': "off"}),
            "end_date": forms.DateTimeInput(format='%Y-%m-%d', attrs={'autocomplete': "off"}),
            'version': forms.Select(attrs={'class': "select2"}),
            'demand': forms.Select(attrs={'class': "select2"}),
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
