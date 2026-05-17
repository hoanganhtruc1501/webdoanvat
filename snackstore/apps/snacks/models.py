from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Ten danh muc")
    description = models.TextField(blank=True, null=True, verbose_name="Mo ta")
    slug = models.SlugField(unique=True, max_length=200, blank=True, null=True, verbose_name="Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngay tao")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngay cap nhat")
    is_active = models.BooleanField(default=True, verbose_name="Kich hoat")

    class Meta:
        verbose_name = "Danh muc"
        verbose_name_plural = "Danh muc"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_snacks_count(self):
        return self.snacks.count()

    get_snacks_count.short_description = 'So san pham'


class Snack(models.Model):
    title = models.CharField(max_length=200, verbose_name="Ten san pham")
    author = models.CharField(max_length=100, verbose_name="Thuong hieu")
    slug = models.SlugField(unique=True, max_length=200, blank=True, null=True)
    description = models.TextField(verbose_name="Mo ta")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Gia")
    discount = models.DecimalField(max_digits=5, decimal_places=0, default=0.00, verbose_name="Giam gia (%)")
    stock = models.IntegerField(verbose_name="So luong ton kho")
    image = models.ImageField(upload_to='snacks/', blank=True, null=True, verbose_name="Hinh anh")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='snacks',
        verbose_name="Danh muc",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'snacks_book'
        verbose_name = "San pham"
        verbose_name_plural = "San pham"
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_discounted_price(self):
        """Tinh gia sau khi giam gia."""
        if self.discount > 0:
            discount_amount = (self.price * self.discount) / 100
            return self.price - discount_amount
        return self.price