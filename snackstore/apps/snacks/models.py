from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Snack(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200, blank=True, null=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=0)
    discount = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='snacks/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='snacks')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_discounted_price(self):
        if self.discount > 0:
            return self.price - (self.price * self.discount / 100)
        return self.price

    def __str__(self):
        return self.name
