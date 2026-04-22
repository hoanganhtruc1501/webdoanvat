from django.shortcuts import render

# Create your views here.
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from snacks.models import Snack


def get_cart(request):
    session_key = getattr(settings, "CART_SESSION_ID", "cart")
    return request.session.get(session_key, {})


def save_cart(request, cart):
    session_key = getattr(settings, "CART_SESSION_ID", "cart")
    request.session[session_key] = cart
    request.session.modified = True


def cart_view(request):
    cart = get_cart(request)
    cart_items = []
    total_price = Decimal("0")
    total_quantity = 0

    for snack_id, quantity in cart.items():
        try:
            snack = Snack.objects.get(id=int(snack_id), is_active=True)
        except Snack.DoesNotExist:
            continue

        unit_price = snack.get_discounted_price()
        item_total = unit_price * quantity

        cart_items.append(
            {
                "snack": snack,
                "quantity": quantity,
                "unit_price": unit_price,
                "item_total": item_total,
            }
        )

        total_price += item_total
        total_quantity += quantity

    context = {
        "cart_items": cart_items,
        "total_price": total_price,
        "total_quantity": total_quantity,
        "page_title": "Giỏ hàng của bạn",
    }
    return render(request, "carts/cart_detail.html", context)


def add_to_cart(request, snack_id):
    snack = get_object_or_404(Snack, id=snack_id, is_active=True)

    if snack.stock <= 0:
        messages.error(request, f'Sản phẩm "{snack.name}" đã hết hàng!')
        return redirect(request.META.get("HTTP_REFERER", "/"))

    quantity = 1
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
            if quantity <= 0:
                quantity = 1
        except (TypeError, ValueError):
            quantity = 1

    cart = get_cart(request)
    snack_id_str = str(snack_id)

    current_quantity = cart.get(snack_id_str, 0)
    new_quantity = current_quantity + quantity

    if new_quantity > snack.stock:
        messages.warning(request, f'Chỉ còn {snack.stock} "{snack.name}" trong kho!')
        return redirect(request.META.get("HTTP_REFERER", "/"))

    cart[snack_id_str] = new_quantity
    save_cart(request, cart)

    messages.success(request, f'Đã thêm "{snack.name}" vào giỏ hàng!')
    return redirect(request.META.get("HTTP_REFERER", "/"))


def update_cart(request, snack_id):
    if request.method != "POST":
        return redirect("carts:detail")

    snack = get_object_or_404(Snack, id=snack_id, is_active=True)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity <= 0:
        return remove_from_cart(request, snack_id)

    if quantity > snack.stock:
        messages.warning(request, f'Chỉ còn {snack.stock} "{snack.name}" trong kho!')
        return redirect("carts:detail")

    cart = get_cart(request)
    cart[str(snack_id)] = quantity
    save_cart(request, cart)

    messages.success(request, f'Đã cập nhật số lượng "{snack.name}"!')
    return redirect("carts:detail")


def remove_from_cart(request, snack_id):
    cart = get_cart(request)
    snack_id_str = str(snack_id)

    if snack_id_str in cart:
        del cart[snack_id_str]
        save_cart(request, cart)

    messages.success(request, "Đã xóa sản phẩm khỏi giỏ hàng!")
    return redirect("carts:detail")


def clear_cart(request):
    save_cart(request, {})
    messages.success(request, "Đã xóa toàn bộ giỏ hàng!")
    return redirect("carts:detail")


def get_cart_count(request):
    cart = get_cart(request)
    return JsonResponse({"count": sum(cart.values())})
