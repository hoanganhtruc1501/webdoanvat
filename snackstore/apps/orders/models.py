from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Promotion(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("percent", "Giảm theo phần trăm"),
        ("fixed", "Giảm số tiền cố định"),
    ]

    code = models.CharField(max_length=30, unique=True, verbose_name="Mã giảm giá")
    description = models.CharField(max_length=255, blank=True, verbose_name="Mô tả")
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default="percent",
        verbose_name="Kiểu giảm giá",
    )
    value = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Giá trị giảm")
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="Giá trị đơn hàng tối thiểu",
    )
    max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Mức giảm tối đa",
    )
    start_at = models.DateTimeField(null=True, blank=True, verbose_name="Ngày bắt đầu")
    end_at = models.DateTimeField(null=True, blank=True, verbose_name="Ngày kết thúc")
    usage_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name="Số lượt sử dụng")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Đã sử dụng")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mã giảm giá"
        verbose_name_plural = "Mã giảm giá"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    def validate_for_order(self, total_amount):
        now = timezone.now()

        if not self.is_active:
            return False, "Mã giảm giá không còn hoạt động."
        if self.start_at and now < self.start_at:
            return False, "Mã giảm giá chưa đến thời gian sử dụng."
        if self.end_at and now > self.end_at:
            return False, "Mã giảm giá đã hết hạn."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "Mã giảm giá đã hết lượt sử dụng."
        if total_amount < self.min_order_amount:
            return False, "Đơn hàng chưa đạt giá trị tối thiểu để dùng mã này."

        return True, ""

    def calculate_discount(self, total_amount):
        if self.discount_type == "percent":
            discount_amount = (total_amount * self.value) / 100
            if self.max_discount_amount is not None:
                discount_amount = min(discount_amount, self.max_discount_amount)
        else:
            discount_amount = self.value

        return min(discount_amount, total_amount)


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
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Mã giảm giá",
    )
    promotion_code = models.CharField(max_length=30, blank=True, verbose_name="Mã giảm giá đã dùng")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Tiền giảm")
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
        return self.total_amount - self.discount_amount + self.shipping_fee


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
