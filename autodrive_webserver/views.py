from django.http import HttpResponse
from django.shortcuts import render


def test_html(request):
    return render(request, "test.html")



