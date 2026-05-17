from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import HomeComment, Review


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user 


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(attrs={"class": "review-control"}),
            "comment": forms.Textarea(
                attrs={
                    "class": "review-control",
                    "rows": 4,
                    "placeholder": "Nhập cảm nhận của bản về sản phẩm",
                }
            ),
        }

class HomeCommentForm(forms.ModelForm):
    class Meta:
        model = HomeComment
        fields = ("comment",)
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "home-comment-control",
                    "rows": 5,
                    "placeholder": "Chia sẻ trải nghiệm của bạn tại Snackstore",
                }
            ),
        }

