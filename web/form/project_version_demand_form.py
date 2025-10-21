from django import forms
from web.models import ProjectVersion, ProjectDemand


class version_form(forms.ModelForm):
    class Meta:
        fields = '__all__'
        model = ProjectVersion


class demand_form(forms.ModelForm):
    class Meta:
        fields = '__all__'
        model = ProjectDemand
