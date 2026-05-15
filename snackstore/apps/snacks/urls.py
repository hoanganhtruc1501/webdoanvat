from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'snacks'

urlpatterns = [

    # Phía người dùng
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    path('', views.snack_list_view, name='list'),              # /snacks/ - Danh sách sản phẩm
    path('<slug:slug>/', views.snack_detail_view, name='detail'), # /snacks/ten-san-pham/ - Chi tiết sản phẩm

]
