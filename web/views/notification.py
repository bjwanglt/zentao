from django.shortcuts import render
from django.http import HttpRequest


def show_iframe(request: HttpRequest):
    return render(request, 'web/notification/iframe.html')
