from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name",
            "email",
            "phone",
            "address",
            "city",
            "district",
            "ward",
            "payment_method",
            "notes",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nhập họ và tên"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "example@email.com"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "0123456789"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Số nhà, tên đường..."}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tỉnh/Thành phố"}),
            "district": forms.TextInput(attrs={"class": "form-control", "placeholder": "Quận/Huyện"}),
            "ward": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phường/Xã"}),
            "payment_method": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Ghi chú thêm (nếu có)"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            full_name = f"{user.first_name} {user.last_name}".strip()
            if full_name:
                self.fields["full_name"].initial = full_name
            self.fields["email"].initial = user.email

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        phone = "".join(ch for ch in phone if ch.isdigit())

        if len(phone) < 10 or len(phone) > 11:
            raise forms.ValidationError("Số điện thoại không hợp lệ.")

        return phone
