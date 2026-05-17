from django.contrib import admin

from .models import Category, Snack


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Snack)
class SnackAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "price", "discount", "stock")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "author")
    list_filter = ("category",)