
# Create your views here.
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from .models import MenuItem, Category, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CategorySerializer, UserSerializer, CartSerializer,  OrderSerializer
from .permissions import IsManager, IsNotCustomer



class MenuItemViewSet (viewsets.ModelViewSet):
    model = MenuItem
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    search_fields = ['category__title']
    ordering_fields = ['price']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManager()]


class CategoryViewSet (viewsets.ModelViewSet):
    model = Category
    serializer_class = CategorySerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Category.objects.all()
    search_fields = ['title']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsManager()]


class ManagerGroupViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsManager, IsAdminUser]
    serializer_class = UserSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    query_set = User.objects.all()
    def list(self, request):
        users = User.objects.all().filter(groups__name='Manager')
        items = UserSerializer(users, many=True)
        return Response(items.data)

    def create(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        managers = Group.objects.get(name="Manager")
        managers.user_set.add(user)
        return Response({"detail": f'user {user.username} added to the Manager group'}, 201)

    def destroy(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        return Response({"detail": f'user {user.username} removed from the Manager group'}, 200)


class DeliveryCrewGroupViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsManager, IsAdminUser]
    serializer_class = UserSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    query_set = User.objects.all()
    def list(self, request):
        users = User.objects.all().filter(groups__name='Delivery crew')
        items = UserSerializer(users, many=True)
        return Response(items.data)

    def create(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        managers = Group.objects.get(name="Delivery crew")
        managers.user_set.add(user)
        return Response({"detail": f'user {user.username} added to the Delivery crew group'}, 201)

    def destroy(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name="Delivery crew")
        managers.user_set.remove(user)
        return Response({"detail": f'user {user.username} removed from the Delivery crew group'}, 200)


class CartView(viewsets.GenericViewSet, generics.ListCreateAPIView,):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        return Cart.objects.all().filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        Cart.objects.all().filter(user=self.request.user).delete()
        return Response("Deleted", 200)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        if self.request.user.groups.count() == 0:
            return Order.objects.all().filter(user=self.request.user)
        elif self.request.user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.all().filter(delivery_crew=self.request.user)
        else:
            return Order.objects.all()

    def create(self, request, *args, **kwargs):
        menuitem_count = Cart.objects.all().filter(user=self.request.user).count()
        if menuitem_count == 0:
            return Response({"detail:": "no items in cart"}, 400)
        data = request.data.copy()
        total_price = 0
        items = Cart.objects.all().filter(user=self.request.user).all()
        for item in items.values():
            total_price += item['price']
        data['total'] = total_price
        data['user'] = self.request.user.id
        order_serializer = OrderSerializer(data=data)
        if order_serializer.is_valid(raise_exception=True):
            order = order_serializer.save()
            for item in items.values():
                orderitem = OrderItem(
                    order=order,
                    menuitem_id=item['menuitem_id'],
                    unit_price=item['unit_price'],
                    price= item['price'],
                    quantity=item['quantity'],
                )
                orderitem.save()

            Cart.objects.all().filter(user=self.request.user).delete()
            return Response(order_serializer.data)

    def update(self, request, *args, **kwargs):
        if self.request.user.groups.filter(name='Delivery crew').exists() and not self.request.user.is_superuser and kwargs['partial'] != True:
            return Response({"detail": "Delivery crew can only do partial update, use Patch instead"}, 403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if self.request.user.groups.filter(name='Delivery crew').exists() and not self.request.user.is_superuser:
            data = request.data
            print(len(data), 'status' not in data)
            if len(data) > 1 or 'status' not in  data:
                return Response({"detail": "Delivery crew can only Update status of order"}, 403)
        return super().partial_update(request, *args, **kwargs)

    def get_permissions(self):
            permission_classes = [IsAuthenticated]
            if self.request.method in ['PUT', 'PATCH']:
                permission_classes = [IsAuthenticated, IsNotCustomer]
            return [permission() for permission in permission_classes]