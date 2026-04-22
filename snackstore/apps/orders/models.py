
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Chờ xử lý"),
        ("processing", "Đang xử lý"),
        ("shipping", "Đang giao"),
        ("completed", "Hoàn thành"),
        ("cancelled", "Đã hủy"),
    ]

    PAYMENT_CHOICES = [
        ("cod", "Thanh toán khi nhận hàng"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Khách hàng",
    )
    full_name = models.CharField(max_length=100, verbose_name="Họ và tên")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    address = models.TextField(verbose_name="Địa chỉ")
    city = models.CharField(max_length=100, verbose_name="Tỉnh/Thành phố")
    district = models.CharField(max_length=100, verbose_name="Quận/Huyện")
    ward = models.CharField(max_length=100, verbose_name="Phường/Xã")
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú")

    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Tổng tiền hàng")
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Phí vận chuyển")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Trạng thái")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="cod", verbose_name="Phương thức thanh toán")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"

    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.full_name}"

    @property
    def final_total(self):
        return self.total_amount + self.shipping_fee


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Đơn hàng",
    )

    
    snack = models.ForeignKey(
        "snacks.Snack",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Sản phẩm",
    )

    snack_name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Đơn giá")

    class Meta:
        verbose_name = "Chi tiết đơn hàng"
        verbose_name_plural = "Chi tiết đơn hàng"

    def __str__(self):
        return f"{self.snack_name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity

