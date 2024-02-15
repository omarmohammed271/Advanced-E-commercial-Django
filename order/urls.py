from django.urls import path
from . import views
app_name = 'order'
urlpatterns = [

    path('payments/',views.payments,name='payments'),
    path('place_order/',views.place_order,name='place_order'),
    path('order_complete/',views.order_complete,name='order_complete'),
    
    
]