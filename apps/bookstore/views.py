from django.shortcuts import render
from .models import Book
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.db.models import F, Q


# Create your views here.

def all_books(request):
    if request.method == "GET":
        # all_book = Book.objects.all()
        all_book = Book.objects.filter(is_active=True)
        # 过滤查找pub为”SEU“的数据
        books = Book.objects.filter(pub="SEU")

        # 排除查找
        books = Book.objects.exclude(pub="SEU")

        # 模糊查找
        books = Book.objects.filter(pub__exact="SEU")  # 等词查找
        books = Book.objects.filter(pub__contains="U")  # 包含查找
        books = Book.objects.filter(price__gt=10)  # 大于查找
        books = Book.objects.filter(price__lt=10)  # 小于查找
        books = Book.objects.filter(price__gte=10)  # 大于等于查找
        books = Book.objects.filter(price__range=(10, 15))  # 范围查找
        books = Book.objects.filter(pub__in=["SEU", "HAU"])  # 列表查找

        # bookstore前面不能加/
        return render(request, "bookstore/all_book.html", locals())

    elif request.method == "POST":
        filterInfo = request.POST
        minPrice = filterInfo.get('minPrice')
        maxPrice = filterInfo.get('maxPrice')
        if minPrice == '':
            minPrice = 0.0
        else:
            minPrice = float(minPrice)

        if maxPrice == '':
            maxPrice = 99999
        else:
            maxPrice = float(maxPrice)

        print(minPrice, maxPrice)
        title = filterInfo.get('title', '')

        if title == '':
            all_book = Book.objects.filter(Q(is_active=True) & Q(price__gt=minPrice) & Q(price__lt=maxPrice))
        else:
            all_book = Book.objects.filter(
                Q(is_active=True) & Q(price__gt=minPrice) & Q(price__lt=maxPrice) & Q(title=title))
        # print(all_book.query) #查看sql请求指令
        return render(request, "bookstore/all_book.html", locals())


# 参数由path转换器提供
def update_book(request, book_id):
    try:
        # 查
        book = Book.objects.get(id=book_id, is_active=True)
    except Exception as e:
        print('--update book error is %s' % (e))
        return HttpResponse("--The book is not existed")

    if request.method == "GET":
        return render(request, 'bookstore/update_book.html', locals())
    elif request.method == 'POST':
        print(request.body)
        price = request.POST['price']
        market_price = request.POST['market_price']
        # 改
        book.price = price
        book.market_price = market_price
        # 保存
        book.save()
        return HttpResponseRedirect('/bookstore/all_book')  # 302跳转 再将页面重定向到主页面


def delete_book(request):
    # 通过获取查询字符串book_id拿到要删除的book的id
    # 将其is_active 改为False
    # 302 跳转至all_book
    book_id = request.GET.get('book_id')
    if not book_id:
        return HttpResponse('--请求异常')
    try:
        book = Book.objects.get(id=book_id, is_active=True)
    except Exception as e:
        print('--delete book error %s' % (e))
        return HttpResponse('--delete error, book not exist')

    book.is_active = False
    book.save()
    return HttpResponseRedirect('/bookstore/all_book')


def add_book(request):
    if request.method == "GET":
        return render(request, "bookstore/add_book.html")
    elif request.method != "POST":
        return HttpResponse("--error")

    title = request.POST['title']
    pub = request.POST['pub']
    price = float(request.POST['price'])
    market_price = float(request.POST['market_price'])

    books = Book.objects.filter(title=title)
    if books.count() != 0:
        book = books[0]
        if not book.is_active:
            book.is_active = True
            book.save()
        # books[0].is_active = True, books[0].save() 无法保存
        return HttpResponse('--此书已存在')

    Book.objects.create(title=title, pub=pub, price=price, market_price=market_price, is_active=True)
    return HttpResponseRedirect('/bookstore/all_book')
