from django.contrib import admin
from .models import Category, Snack


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Snack)
class SnackAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "discount", "stock")
    list_filter = ("category",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
