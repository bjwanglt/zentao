from django.urls import path
from web.views import account
from django.shortcuts import HttpResponse, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def login(request):
    return HttpResponse('i am testapp')


class person:
    def __init__(self, name):
        self.name = name


@csrf_exempt
def test_put(request):
    return JsonResponse(dict(age=123))


def to_test_put(request):
    return render(request, 'test_index.html')


urlpatterns = [
    path('login/', login, name='login'),
    path('test_put/', test_put, name='test_put'),
    path('to_test_put/', to_test_put, name='to_test_put'),
]


