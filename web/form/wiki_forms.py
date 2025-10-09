from django.http import HttpRequest

from web.form.FormMixin import BootstrapMixin
from web import models
from django import forms


class wiki_form(BootstrapMixin, forms.ModelForm):
    parent_id = forms.ChoiceField(label='父级', widget=forms.Select(), choices=[], required=False)

    def __init__(self, request: HttpRequest, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        project_wiki = list(models.Wiki.objects.filter(project_id=request.proid).values_list('id', 'title'))
        self.fields['parent_id'].choices = [(None, '请选择')] + project_wiki
        self.fields['content'].required = False

    class Meta:
        model = models.Wiki
        fields = ['title', 'content', 'parent_id']

    def clean_parent_id(self):
        pid = self.cleaned_data['parent_id']
        if not pid:
            pid = None
        return pid


