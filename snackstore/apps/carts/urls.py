from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_view, name="detail"),
    path("add/<int:snack_id>/", views.add_to_cart, name="add"),
    path("update/<int:snack_id>/", views.update_cart, name="update"),
    path("remove/<int:snack_id>/", views.remove_from_cart, name="remove"),
    path("clear/", views.clear_cart, name="clear"),
    path("count/", views.get_cart_count, name="count"),
    path("", views.cart_view, name="detail"),  # /cart/ - Xem giỏ hàng
    path("add/<int:snack_id>/", views.add_to_cart, name="add"),  # /cart/add/1/ - Thêm vào giỏ
    path("update/<int:snack_id>/", views.update_cart, name="update"),  # /cart/update/1/ - Cập nhật số lượng
    path("remove/<int:snack_id>/", views.remove_from_cart, name="remove"),  # /cart/remove/1/ - Xóa khỏi giỏ
    path("clear/", views.clear_cart, name="clear"),  # /cart/clear/ - Xóa toàn bộ giỏ hàng
    path("count/", views.get_cart_count, name="count"),  # /cart/count/ - Lấy số lượng AJAX
]
