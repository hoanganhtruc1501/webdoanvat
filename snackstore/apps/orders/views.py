from decimal import Decimal

from django.apps import apps
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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

    orders = (
        Order.objects.filter(user=request.user)
        .annotate(total_quantity=Sum("items__quantity"))
        .prefetch_related("items")
    )
    return render(request, "orders/order_list.html", {"orders": orders})


def order_create_view(request):
    return redirect("orders:checkout")


def checkout_view(request):
    cart = get_cart(request)

    if not cart:
        messages.warning(request, "Gio hang cua ban dang trong.")
        return redirect("/")

    Snack = apps.get_model("snacks", "Snack")

    cart_items = []
    total_amount = Decimal("0")
    total_quantity = 0

    for snack_id, quantity in cart.items():
        try:
            snack = Snack.objects.get(id=int(snack_id))
        except Snack.DoesNotExist:
            messages.error(request, "Co san pham trong gio hang khong ton tai.")
            return redirect("/")

        if hasattr(snack, "stock") and snack.stock < quantity:
            messages.error(request, f'San pham "{getattr(snack, "title", snack)}" chi con {snack.stock} trong kho.')
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
                        snack_name=getattr(snack, "title", str(snack)),
                        quantity=item["quantity"],
                        price=item["price"],
                    )

                    if hasattr(snack, "stock"):
                        snack.stock -= item["quantity"]
                        snack.save()

                request.session["cart"] = {}
                request.session["last_order_id"] = order.id
                request.session.modified = True

                messages.success(request, f"Dat hang thanh cong. Ma don hang: #{order.id}")
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
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("items__snack"),
        id=order_id,
    )

    if request.user.is_authenticated:
        if order.user and order.user != request.user and not request.user.is_staff:
            raise Http404("Ban khong co quyen xem don hang nay.")
    else:
        last_order_id = request.session.get("last_order_id")
        if last_order_id != order.id:
            raise Http404("Ban khong co quyen xem don hang nay.")

    return render(request, "orders/order_detail.html", {"order": order})


def _can_access_order(request, order):
    if request.user.is_authenticated:
        return not order.user or order.user == request.user or request.user.is_staff
    return request.session.get("last_order_id") == order.id


@require_POST
def order_cancel_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("items__snack"),
        id=order_id,
    )

    if not _can_access_order(request, order):
        raise Http404("Ban khong co quyen huy don hang nay.")

    if order.status != "pending":
        messages.warning(request, "Chi co the huy don hang dang cho xu ly.")
        return redirect("orders:detail", order_id=order.id)

    with transaction.atomic():
        for item in order.items.select_related("snack"):
            if item.snack:
                item.snack.stock += item.quantity
                item.snack.save(update_fields=["stock"])

        order.status = "cancelled"
        order.save(update_fields=["status", "updated_at"])

    messages.success(request, f"Da huy don hang #{order.id}.")
    return redirect("orders:detail", order_id=order.id)
