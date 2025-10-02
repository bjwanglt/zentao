from django import forms
from web import models
from web.form.FormMixin import BootstrapMixin
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from web import models


class AddProjectForm(BootstrapMixin, forms.ModelForm):
    exclude_filed_name = ['color']

    desc = forms.CharField(widget=forms.Textarea(), label='项目描述')
    color = forms.CharField(widget=forms.RadioSelect(choices=models.Project.COLOR_CHOICES, attrs={
        'class': 'color-radio'
    }), label='颜色')

    def __init__(self, request: HttpRequest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    class Meta:
        model = models.Project
        fields = ['name', 'color', 'desc']



