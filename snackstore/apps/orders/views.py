
from decimal import Decimal

from django.apps import apps
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CheckoutForm
from .models import Order, OrderItem


def get_cart(request):
    return request.session.get("cart", {})


def order_list_view(request):
    if not request.user.is_authenticated:
        return render(
            request,
            "orders/order_list.html",
            {
                "orders": [],
                "guest_mode": True,
            },
        )

    orders = Order.objects.filter(user=request.user)
    return render(request, "orders/order_list.html", {"orders": orders})


def order_create_view(request):
    return redirect("orders:checkout")


def checkout_view(request):
    cart = get_cart(request)

    if not cart:
        messages.warning(request, "Giỏ hàng của bạn đang trống.")
        return redirect("/")

    Snack = apps.get_model("snacks", "Snack")

    cart_items = []
    total_amount = Decimal("0")
    total_quantity = 0

    for snack_id, quantity in cart.items():
        try:
            snack = Snack.objects.get(id=int(snack_id))
        except Snack.DoesNotExist:
            messages.error(request, "Có sản phẩm trong giỏ hàng không tồn tại.")
            return redirect("/")

        if hasattr(snack, "stock") and snack.stock < quantity:
            messages.error(request, f'Sản phẩm "{getattr(snack, "name", snack)}" chỉ còn {snack.stock} trong kho.')
            return redirect("/")

        if hasattr(snack, "get_discounted_price") and callable(snack.get_discounted_price):
            price = Decimal(str(snack.get_discounted_price()))
        else:
            price = Decimal(str(snack.price))

        item_total = price * quantity
        cart_items.append(
            {
                "snack": snack,
                "quantity": quantity,
                "price": price,
                "item_total": item_total,
            }
        )
        total_amount += item_total
        total_quantity += quantity

    shipping_fee = Decimal("0") if total_amount >= Decimal("200000") else Decimal("30000")
    final_total = total_amount + shipping_fee

    if request.method == "POST":
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                order.total_amount = total_amount
                order.shipping_fee = shipping_fee
                order.save()

                for item in cart_items:
                    snack = item["snack"]

                    OrderItem.objects.create(
                        order=order,
                        snack=snack,
                        snack_name=getattr(snack, "name", str(snack)),
                        quantity=item["quantity"],
                        price=item["price"],
                    )

                    if hasattr(snack, "stock"):
                        snack.stock -= item["quantity"]
                        snack.save()

                request.session["cart"] = {}
                request.session["last_order_id"] = order.id
                request.session.modified = True

                messages.success(request, f"Đặt hàng thành công. Mã đơn hàng: #{order.id}")
                return redirect("orders:detail", order_id=order.id)
    else:
        form = CheckoutForm(user=request.user)

    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart_items": cart_items,
            "total_amount": total_amount,
            "shipping_fee": shipping_fee,
            "final_total": final_total,
            "total_quantity": total_quantity,
        },
    )


def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.user.is_authenticated:
        if order.user and order.user != request.user and not request.user.is_staff:
            raise Http404("Bạn không có quyền xem đơn hàng này.")
    else:
        last_order_id = request.session.get("last_order_id")
        if last_order_id != order.id:
            raise Http404("Bạn không có quyền xem đơn hàng này.")

    return render(request, "orders/order_detail.html", {"order": order})

