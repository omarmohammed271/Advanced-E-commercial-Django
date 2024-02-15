from django.shortcuts import redirect, render,get_object_or_404
from django.contrib import messages
from store.forms import ReviewForm
from .models import Product, ProductGallery, ReviewRating
from category.models import Category
from cart.models import CartItem
from cart.views import _cart_id
from django.core.paginator import Paginator
from django.db.models import Q
from order.models import OrderProduct

# Create your views here.
def store(request,slug=None):
    if slug != None:
        categories = get_object_or_404(Category,slug=slug)
        product = Product.objects.filter(category=categories,is_available=True)
        paginator = Paginator(product, 3)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number) 
        count = product.count()
    else:    
        product = Product.objects.all().filter(is_available = True).order_by('id')
        paginator = Paginator(product, 3)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        count = product.count()

    context = {
        'products' : page_obj,
        'count' : count,

    }

    return render(request,'store/store.html',context)

def product_detail(request,slug,product_slug):
    product = Product.objects.get(category__slug=slug,slug=product_slug)
    in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request),product=product).exists()
    if request.user.is_authenticated:

        try:
            orderproduct = OrderProduct.objects.filter(user=request.user,product_id=product.id).exists()

        except OrderProduct.DoesNotExist:
            orderproduct=None
    else:
        orderproduct=None
    reviews =  ReviewRating.objects.all()   
    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=product.id)
    context={
        'product' : product,
        'in_cart' :in_cart,
        'orderproduct' :orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        
    }
    return render(request,'store/product_detail.html',context)

def search(request):
    product = None
    count = None
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            product = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            count = product.count()

    context = {
        'products' : product,
        'count' : count,

    }
    return render(request,'store/store.html',context)
def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)