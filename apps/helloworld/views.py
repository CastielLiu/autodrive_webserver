from django.http import HttpResponse
from django.shortcuts import render

from autodrive_webserver import settings
from .models import Image
import os

# Create your views here.


def test_html(request):
    return render(request, "helloworld/test.html")


def a_upload(request):
    if request.method == "POST":
        files = request.FILES.getlist("myfiles")
        if files is None:
            return HttpResponse("请选择需要上传的文件")
        for file in files:
            image = Image()
            image.user = "ceshi"
            image.name = file.name
            image.src = file
            image.save()
    return HttpResponse("ok")
