from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "status",
        "payment_method",
        "total_amount",
        "shipping_fee",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("full_name", "phone", "email")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "snack_name", "quantity", "price")
    search_fields = ("snack_name",)
