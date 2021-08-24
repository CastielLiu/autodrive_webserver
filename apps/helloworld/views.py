from django.http import HttpResponse
from django.shortcuts import render

from autodrive_webserver import settings
from .models import Image
import os
from django.views.decorators.csrf import csrf_exempt

# Create your views here.


def test_html(request):
    return render(request, "helloworld/test.html")


@csrf_exempt
def a_upload(request):
    if request.method == "POST":
        print(request.FILES.getlist('myfiles'))

        print(request.FILES)
        # for files in request.FILES.values():
        #     print(files)

        files = request.FILES.getlist("myfiles")
        if files is None:
            return HttpResponse("请选择需要上传的文件")

        for file in files:
            image = Image()
            image.user = "ceshi"
            image.name = file.name
            image.src = file
            image.save()
            print(image.src.storage.location)
            file_dir = image.src.storage.base_location+image.src.name
            print(file_dir)
            fp = image.src.storage.open(file_dir)

            for chunk in fp.chunks():
                print(chunk)

            pass

    return HttpResponse("ok")
