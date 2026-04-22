from django.urls import path
from . import views

app_name = "carts"

urlpatterns = [
    path("", views.cart_view, name="detail"),
    path("add/<int:snack_id>/", views.add_to_cart, name="add"),
    path("update/<int:snack_id>/", views.update_cart, name="update"),
    path("remove/<int:snack_id>/", views.remove_from_cart, name="remove"),
    path("clear/", views.clear_cart, name="clear"),
    path("count/", views.get_cart_count, name="count"),
]
