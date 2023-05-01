from django.contrib import admin
from .models import Category, MenuItem, Order, OrderItem
# Register your models here.
admin.site.register(MenuItem)
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(OrderItem)
