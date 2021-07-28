from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


# Create your views here.

def main_page(request):
    return render(request, 'autodrive/index.html')


def test_page(request):
    return render(request, 'autodrive/test.html')
