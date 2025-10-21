from django.http import HttpRequest
from django.shortcuts import render


def to_config(request: HttpRequest, pid):
    return render(request, 'web/config/config.html', dict())
