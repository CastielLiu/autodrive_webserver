from django.http import HttpResponse
from django.shortcuts import render


def test_html(request):
    return render(request, "test.html")


def vehicleState(request):
    res = HttpResponse('{"speed": "10.0", "battery": "0.5"}')
    return res
