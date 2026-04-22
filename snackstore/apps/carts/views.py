from django.shortcuts import render

# Create your views here.
from decimal import Decimal

from django.apps import apps
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render


CART_SESSION_ID = "cart"


def get_snack_model():
    return apps.get_model("snacks", "Snack")


def get_cart(request):
    """Lấy giỏ hàng từ session."""
    cart = request.session.get(CART_SESSION_ID, {})
    return cart if isinstance(cart, dict) else {}


def save_cart(request, cart):
    """Lưu giỏ hàng vào session."""
    request.session[CART_SESSION_ID] = cart
    request.session.modified = True


def get_snack_name(snack):
    return getattr(snack, "title", getattr(snack, "name", str(snack)))


def get_snack_price(snack):
    if hasattr(snack, "get_discounted_price") and callable(snack.get_discounted_price):
        return Decimal(str(snack.get_discounted_price()))

    return Decimal(str(getattr(snack, "price", 0)))


def get_quantity(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def redirect_back(request, fallback="snacks:list"):
    return redirect(request.META.get("HTTP_REFERER") or fallback)


def cart_view(request):
    """Xem giỏ hàng."""
    Snack = get_snack_model()
    cart = get_cart(request)
    cleaned_cart = {}
    cart_items = []
    total_price = Decimal("0")
    total_quantity = 0

    for snack_id, quantity in cart.items():
        snack_id = str(snack_id)
        quantity = get_quantity(quantity)

        if quantity <= 0:
            continue

        try:
            snack = Snack.objects.get(id=int(snack_id))
        except (Snack.DoesNotExist, ValueError):
            continue

        price = get_snack_price(snack)
        item_total = price * quantity

        cart_items.append(
            {
                "snack": snack,
                "quantity": quantity,
                "price": price,
                "discounted_price": price,
                "item_total": item_total,
            }
        )
        cleaned_cart[snack_id] = quantity
        total_price += item_total
        total_quantity += quantity

    if cleaned_cart != cart:
        save_cart(request, cleaned_cart)

    context = {
        "cart_items": cart_items,
        "total_price": total_price,
        "total_quantity": total_quantity,
        "page_title": "Giỏ hàng của bạn",
    }
    return render(request, "carts/cart_detail.html", context)


def add_to_cart(request, snack_id):
    """Thêm sản phẩm vào giỏ hàng."""
    Snack = get_snack_model()
    snack = get_object_or_404(Snack, id=snack_id)
    snack_name = get_snack_name(snack)
    stock = getattr(snack, "stock", None)

    if stock is not None and stock <= 0:
        messages.error(request, f'Sản phẩm "{snack_name}" đã hết hàng!')
        return redirect_back(request)

    quantity = 1
    if request.method == "POST":
        quantity = max(get_quantity(request.POST.get("quantity", 1)), 1)

    cart = get_cart(request)
    snack_id_str = str(snack_id)
    current_quantity = get_quantity(cart.get(snack_id_str, 0), 0)
    new_quantity = current_quantity + quantity

    if stock is not None and new_quantity > stock:
        messages.warning(request, f'Chỉ còn {stock} sản phẩm "{snack_name}" trong kho!')
        return redirect_back(request)

    cart[snack_id_str] = new_quantity
    save_cart(request, cart)

    if current_quantity:
        messages.success(request, f'Đã cập nhật số lượng "{snack_name}" trong giỏ hàng!')
    elif quantity == 1:
        messages.success(request, f'Đã thêm "{snack_name}" vào giỏ hàng!')
    else:
        messages.success(request, f'Đã thêm {quantity} sản phẩm "{snack_name}" vào giỏ hàng!')

    return redirect_back(request)


def update_cart(request, snack_id):
    """Cập nhật số lượng sản phẩm trong giỏ hàng."""
    if request.method != "POST":
        return redirect("cart:detail")

    Snack = get_snack_model()
    snack = get_object_or_404(Snack, id=snack_id)
    snack_name = get_snack_name(snack)
    quantity = get_quantity(request.POST.get("quantity", 1))

    if quantity <= 0:
        return remove_from_cart(request, snack_id)

    stock = getattr(snack, "stock", None)
    if stock is not None and quantity > stock:
        messages.warning(request, f'Chỉ còn {stock} sản phẩm "{snack_name}" trong kho!')
        return redirect("cart:detail")

    cart = get_cart(request)
    cart[str(snack_id)] = quantity
    save_cart(request, cart)

    messages.success(request, f'Đã cập nhật số lượng "{snack_name}"!')
    return redirect("cart:detail")


def remove_from_cart(request, snack_id):
    """Xóa sản phẩm khỏi giỏ hàng."""
    Snack = get_snack_model()
    snack = get_object_or_404(Snack, id=snack_id)
    snack_id_str = str(snack_id)
    cart = get_cart(request)

    if snack_id_str in cart:
        del cart[snack_id_str]
        save_cart(request, cart)
        messages.success(request, f'Đã xóa "{get_snack_name(snack)}" khỏi giỏ hàng!')

    return redirect("cart:detail")


def clear_cart(request):
    """Xóa toàn bộ giỏ hàng."""
    save_cart(request, {})
    messages.success(request, "Đã xóa toàn bộ giỏ hàng!")
    return redirect("cart:detail")


def get_cart_count(request):
    """Lấy tổng số lượng sản phẩm trong giỏ hàng."""
    cart = get_cart(request)
    count = sum(max(get_quantity(quantity, 0), 0) for quantity in cart.values())
    return JsonResponse({"count": count})


