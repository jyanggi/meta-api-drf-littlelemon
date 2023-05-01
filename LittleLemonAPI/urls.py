
from django.urls import path, include
from rest_framework import routers

from . import views


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'menu-items', views.MenuItemViewSet)
router.register(r'category', views.CategoryViewSet)
router.register(r'groups/manager/users', views.ManagerGroupViewSet, basename='groups-manager-users')
router.register(r'groups/delivery-crew/users', views.DeliveryCrewGroupViewSet, basename='groups-delivery-crew-users')
router.register(r'orders', views.OrderViewSet )
router.register(r'cart/menu-items', views.CartView )

urlpatterns = [
    path('', include(router.urls)),
]
