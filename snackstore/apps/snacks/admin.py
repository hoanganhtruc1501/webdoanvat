from django.contrib import admin

from .models import Category, Snack, Review, HomeComment


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

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("snack", "user", "rating", "is_active", "created_at")
    list_filter = ("rating", "is_active", "created_at")
    search_fields = ("snack__title", "user__username", "comment")


@admin.register(HomeComment)
class HomeCommentAdmin(admin.ModelAdmin):
    list_display = ("user", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "comment")
