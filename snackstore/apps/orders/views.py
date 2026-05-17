from decimal import Decimal

from django.apps import apps
from django.contrib import messages
from django.db import transaction
from django.db.models import F, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CheckoutForm
from .models import Order, OrderItem, Promotion


def get_cart(request):
    return request.session.get("cart", {})


def get_valid_promotion(code, total_amount):
    code = (code or "").strip().upper()
    if not code:
        return None, Decimal("0"), ""

    try:
        promotion = Promotion.objects.get(code__iexact=code)
    except Promotion.DoesNotExist:
        return None, Decimal("0"), "Mã giảm giá không tồn tại."

    is_valid, message = promotion.validate_for_order(total_amount)
    if not is_valid:
        return None, Decimal("0"), message

    return promotion, promotion.calculate_discount(total_amount), ""


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
            messages.error(request, f'Sản phẩm "{getattr(snack, "title", snack)}" chỉ còn {snack.stock} trong kho.')
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
    promotion_code = request.session.get("promotion_code", "")

    if request.method == "POST" and "remove_promotion" in request.POST:
        request.session.pop("promotion_code", None)
        messages.success(request, "Đã xoá mã giảm giá.")
        return redirect("orders:checkout")

    if request.method == "POST" and "apply_promotion" in request.POST:
        submitted_code = request.POST.get("promotion_code", "")
        promotion, discount_amount, promotion_error = get_valid_promotion(submitted_code, total_amount)
        if promotion_error:
            request.session.pop("promotion_code", None)
            messages.error(request, promotion_error)
        else:
            request.session["promotion_code"] = promotion.code
            messages.success(request, f"Đã áp dụng mã giảm giá {promotion.code}.")
        request.session.modified = True
        return redirect("orders:checkout")

    if request.method == "POST":
        promotion_code = request.POST.get("promotion_code", promotion_code).strip().upper()

    promotion, discount_amount, promotion_error = get_valid_promotion(promotion_code, total_amount)
    if promotion_error and promotion_code == request.session.get("promotion_code", ""):
        request.session.pop("promotion_code", None)
        request.session.modified = True
        promotion_code = ""
        promotion_error = ""

    final_total = total_amount - discount_amount + shipping_fee

    if request.method == "POST":
        form = CheckoutForm(request.POST, user=request.user)
        if promotion_error:
            form.add_error(None, promotion_error)
        if not promotion_error and form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                order.total_amount = total_amount
                order.shipping_fee = shipping_fee
                order.promotion = promotion
                order.promotion_code = promotion.code if promotion else ""
                order.discount_amount = discount_amount
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

                if promotion:
                    Promotion.objects.filter(pk=promotion.pk).update(used_count=F("used_count") + 1)

                request.session["cart"] = {}
                request.session.pop("promotion_code", None)
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
            "promotion": promotion,
            "promotion_code": promotion_code,
            "discount_amount": discount_amount,
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
            raise Http404("Bạn không có quyền xem đơn hàng này.")
    else:
        last_order_id = request.session.get("last_order_id")
        if last_order_id != order.id:
            raise Http404("Bạn không có quyền xem đơn hàng này.")

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
        raise Http404("Bạn không có quyền xem đơn hàng này.")

    if order.status != "pending":
        messages.warning(request, "Chỉ có thể huỷ đơn hàng đang chờ xử lý.")
        return redirect("orders:detail", order_id=order.id)

    with transaction.atomic():
        for item in order.items.select_related("snack"):
            if item.snack:
                item.snack.stock += item.quantity
                item.snack.save(update_fields=["stock"])

        order.status = "cancelled"
        order.save(update_fields=["status", "updated_at"])
        
    messages.success(request, f"Đã huỷ đơn hàng #{order.id}.")
    return redirect("orders:detail", order_id=order.




                    
