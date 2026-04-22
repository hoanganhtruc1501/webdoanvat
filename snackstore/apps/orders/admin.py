from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("snack", "snack_name", "quantity", "price", "get_total_price")
    readonly_fields = ("snack", "snack_name", "quantity", "price", "get_total_price")

    @admin.display(description="Thành tiền")
    def get_total_price(self, obj):
        if not obj:
            return "0₫"
        return f"{obj.subtotal:,.0f}₫"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "full_name",
        "email",
        "phone",
        "status",
        "payment_method",
        "total_amount",
        "shipping_fee",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "created_at", "city"]
    search_fields = ["id", "full_name", "email", "phone"]
    readonly_fields = ["created_at", "updated_at", "get_total_with_shipping"]
    inlines = [OrderItemInline]

    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("user", "status", "payment_method"),
        }),
        ("Thông tin khách hàng", {
            "fields": ("full_name", "email", "phone"),
        }),
        ("Địa chỉ giao hàng", {
            "fields": ("address", "ward", "district", "city"),
        }),
        ("Thông tin thanh toán", {
            "fields": ("total_amount", "shipping_fee", "get_total_with_shipping"),
        }),
        ("Ghi chú", {
            "fields": ("notes",),
        }),
        ("Thời gian", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="Tổng tiền (bao gồm ship)")
    def get_total_with_shipping(self, obj):
        if not obj:
            return "0₫"
        return f"{obj.final_total:,.0f}₫"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "snack_name", "quantity", "price", "get_total_price"]
    list_filter = ["order__created_at"]
    search_fields = ["order__id", "snack_name", "order__full_name"]

    @admin.display(description="Thành tiền")
    def get_total_price(self, obj):
        return f"{obj.subtotal:,.0f}₫"
