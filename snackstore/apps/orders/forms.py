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
        labels = {
            "full_name": "Họ và tên",
            "email": "Email",
            "phone": "Số điện thoại",
            "address": "Địa chỉ",
            "city": "Tỉnh/Thành phố",
            "district": "Quận/Huyện",
            "ward": "Phường/Xã",
            "payment_method": "Phương thức thanh toán",
            "notes": "Ghi chú",
        }
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nhập họ và tên đầy đủ",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "example@email.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0123456789",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Số nhà, tên đường...",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tỉnh/Thành phố",
                }
            ),
            "district": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Quận/Huyện",
                }
            ),
            "ward": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phường/Xã",
                }
            ),
            "payment_method": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Ghi chú đặc biệt (tuỳ chọn)",
                }
            ),
        }
        error_messages = {
            "full_name": {
                "required": "Vui lòng nhập họ và tên.",
            },
            "email": {
                "required": "Vui lòng nhập email.",
                "invalid": "Email không hợp lệ.",
            },
            "phone": {
                "required": "Vui lòng nhập số điện thoại.",
            },
            "address": {
                "required": "Vui lòng nhập địa chỉ giao hàng.",
            },
            "city": {
                "required": "Vui lòng nhập tỉnh/thành phố.",
            },
            "district": {
                "required": "Vui lòng nhập quận/huyện.",
            },
            "ward": {
                "required": "Vui lòng nhập phường/xã.",
            },
            "payment_method": {
                "required": "Vui lòng chọn phương thức thanh toán.",
            },
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            full_name = f"{user.first_name} {user.last_name}".strip()
            self.fields["full_name"].initial = full_name or user.get_username()
            self.fields["email"].initial = user.email

    def clean_full_name(self):
        full_name = self.cleaned_data.get("full_name", "")
        return " ".join(full_name.split())

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")

        phone = "".join(filter(str.isdigit, phone))
        if len(phone) < 10 or len(phone) > 11:
            raise forms.ValidationError("Số điện thoại không hợp lệ.")

        return phone
