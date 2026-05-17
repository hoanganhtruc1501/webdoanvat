from django.db import models
from django.db.models import Avg
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    slug = models.SlugField(unique=True, max_length=200, blank=True, null=True, verbose_name="Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_snacks_count(self):
        return self.snacks.count()

    get_snacks_count.short_description = 'Số sản phẩm'


class Snack(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    author = models.CharField(max_length=100, verbose_name="Thương hiệu")
    slug = models.SlugField(unique=True, max_length=200, blank=True, null=True)
    description = models.TextField(verbose_name="Mô tả")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá")
    discount = models.DecimalField(max_digits=5, decimal_places=0, default=0.00, verbose_name="Giảm giá (%)")
    stock = models.IntegerField(verbose_name="Số lượng tồn kho")
    image = models.ImageField(upload_to='snacks/', blank=True, null=True, verbose_name="Hình ảnh")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='snacks',
        verbose_name="Danh mục",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'snacks_book'
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_discounted_price(self):
        """Tính giá sau khi giảm giá."""
        if self.discount > 0:
            discount_amount = (self.price * self.discount) / 100
            return self.price - discount_amount
        return self.price

    @property
    def average_rating(self):
        rating = self.reviews.filter(is_active=True).aggregate(avg=Avg("rating"))["avg"]
        return round(rating, 1) if rating else 0

    @property
    def review_count(self):
        return self.reviews.filter(is_active=True).count()


class Review(models.Model):
    RATING_CHOICES = [(value, f"{value} sao") for value in range(1, 6)]

    snack = models.ForeignKey(
        Snack,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Sản phẩm",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="snack_reviews",
        verbose_name="Người dùng",
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name="Số sao")
    comment = models.TextField(verbose_name="Nội dung đánh giá")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Đánh giá sản phẩm"
        verbose_name_plural = "Đánh giá sản phẩm"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["snack", "user"], name="unique_review_per_user_snack")
        ]

    def __str__(self):
        return f"{self.snack.title} - {self.user.username} ({self.rating} sao)"


    class HomeComment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="home_comments",
        verbose_name="Người dùng",
    )
    comment = models.TextField(verbose_name="Nội dung comment")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Comment trang chủ"
        verbose_name_plural = "Comment trang chủ"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.comment[:40]}"
