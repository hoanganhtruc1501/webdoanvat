from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list_view, name="list"),
    path("create/", views.order_create_view, name="create"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("<int:order_id>/", views.order_detail_view, name="detail"),
]
