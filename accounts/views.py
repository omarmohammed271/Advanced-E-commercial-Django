from django.shortcuts import get_object_or_404, render,redirect
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required

from order.models import Order, OrderProduct
from .form import RegisterationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from cart.models import Cart,CartItem
from cart.views import _cart_id
import requests

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegisterationForm(request.POST)
        
        if form.is_valid():
            
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            user_name = email.split('@')[0]
            
            user = Account.objects.create_user(
                first_name=first_name,last_name=last_name,email=email,username=user_name,password=password
            )
            user.phone_number = phone_number
            user.save()

            # user Activation
            current_site = get_current_site(request)
            mail_subject = "please Activate your Account"
            message = render_to_string('accounts/activate_email.html',{
                'user' : user,
                'domain' : current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user),
            })
            to_email = email
            send_mail = EmailMessage(mail_subject,message,to=[to_email])
            send_mail.send()

            # messages.success(request,"Registeration Succussful")
            return redirect('/accounts/login/?command=verification&email='+email)
            

    else:
        form = RegisterationForm()
    context = {
        'form' : form,
    }
    return render(request,'accounts/register.html',context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email,password=password)

        if user is not None:
            try:
                
                cart = Cart.objects.get(cart_id=_cart_id(request))
                
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists() 
                print(is_cart_item_exists) 
                if is_cart_item_exists:
                    
                    cart_item = CartItem.objects.filter(cart=cart)

                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))
                    #get the cart item from user to access his product variation
                    cart_item = CartItem.objects.filter(user=user)  
                    ex_var_list = []
                    id = []  
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]   
                            item = CartItem.objects.get(id=item_id) 
                            item.quantity += 1
                            item.user = user
                            item.save()   
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()  
                        

            except:
                
                pass   

            auth.login(request,user)
            messages.success(request,'You Logged Successfully')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # print(query,'*********************')
                params = dict(x.split('=') for x in query.split('&'))
                print(params,'***********')
                if 'next' in params:
                    nextpage = params['next'] 
                    print(redirect(nextpage))
                    
                    return redirect(nextpage)
            except:
                return redirect('accounts:dashboard')

        else:
            messages.error(request,"Invalid Login")
            return redirect('accounts:login')
    return render(request,'accounts/login.html')
@login_required(login_url='accounts:login')
def logout(request):
    auth.logout(request)
    messages.success(request,"Logged out Successfully")

    return redirect('accounts:login') 

def activate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active = True
        user.save()
        messages.success(request,'Congratulations! Your account is activated.')  
        return redirect("accounts:login") 
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('accounts:register')    
@login_required(login_url='accounts:login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    userprofile = UserProfile.objects.get(user_id=request.user.id)
    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }
    return render (request,'accounts/dashboard.html',context)    

def forgetpassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # user Activation
            current_site = get_current_site(request)
            mail_subject = "please Set new password"
            message = render_to_string('accounts/reset_password_email.html',{
                'user' : user,
                'domain' : current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user),
            })
            to_email = email
            send_mail = EmailMessage(mail_subject,message,to=[to_email])
            send_mail.send()
            return redirect('accounts:login')
        else:
            messages.error(request,"No Account has this Email")
            return redirect('accounts:forgetpassword')

    return render(request,'accounts/forgetpassword.html')
def reset_validate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid'] = uid
        messages.success(request,'Please set your Password')
        return redirect('accounts:resetpassword')
    else:
        messages.error(request,'this link has been expired')
        return redirect('accounts:login')
    
    

def resetpassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session['uid']
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'Your password changed successfully')
            return redirect('accounts:login')
        else:
            messages.error(request,'Passord does not match')
            return redirect('accounts:resetpassword')
    else:    
        return render(request,'accounts/resetpassword.html')

@login_required(login_url='accounts:login')
def my_orders(request):

    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)

@login_required(login_url='accounts:login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='accounts:login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Password updated successfully.')
                return redirect('accounts:change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('accounts:change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('accounts:change_password')
    return render(request, 'accounts/change_password.html')


@login_required(login_url='accounts:login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)

