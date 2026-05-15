from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.detail_view, name='detail'),
    path('add/<int:snack_id>/', views.add_view, name='add'),
    path('update/<int:snack_id>/', views.update_view, name='update'),
    path('remove/<int:snack_id>/', views.remove_view, name='remove'),
    path('clear/', views.clear_view, name='clear'),
]
