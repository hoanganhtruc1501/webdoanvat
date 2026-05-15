from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from snacks.models import Snack


def _get_cart(request):
    return request.session.get('cart', {})


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _item_price(snack):
    if hasattr(snack, 'get_discounted_price') and callable(snack.get_discounted_price):
        return Decimal(str(snack.get_discounted_price()))
    return Decimal(str(snack.price))


def detail_view(request):
    cart = _get_cart(request)
    cart_items = []
    total_amount = Decimal('0')
    total_quantity = 0
    changed = False

    for snack_id, quantity in list(cart.items()):
        try:
            snack = Snack.objects.get(id=int(snack_id))
            quantity = max(1, int(quantity))
        except (Snack.DoesNotExist, ValueError, TypeError):
            cart.pop(snack_id, None)
            changed = True
            continue

        if snack.stock <= 0:
            cart.pop(snack_id, None)
            changed = True
            continue

        if quantity > snack.stock:
            quantity = snack.stock
            cart[str(snack.id)] = quantity
            changed = True

        price = _item_price(snack)
        item_total = price * quantity
        cart_items.append({
            'snack': snack,
            'quantity': quantity,
            'price': price,
            'item_total': item_total,
        })
        total_amount += item_total
        total_quantity += quantity

    if changed:
        _save_cart(request, cart)

    shipping_fee = Decimal('0') if total_amount >= Decimal('200000') or total_amount == 0 else Decimal('30000')
    final_total = total_amount + shipping_fee

    return render(request, 'cart/cart_detail.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'shipping_fee': shipping_fee,
        'final_total': final_total,
        'total_quantity': total_quantity,
    })


def add_view(request, snack_id):
    snack = get_object_or_404(Snack, id=snack_id)
    if snack.stock <= 0:
        messages.warning(request, 'Sản phẩm này đang hết hàng.')
        return redirect(request.META.get('HTTP_REFERER', 'snacks:list'))

    item_key = str(snack_id)
    cart = _get_cart(request)
    quantity = 1
    if request.method == 'POST':
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))
        except (ValueError, TypeError):
            quantity = 1

    current_quantity = int(cart.get(item_key, 0))
    cart[item_key] = min(current_quantity + quantity, snack.stock)
    _save_cart(request, cart)
    messages.success(request, 'Đã thêm sản phẩm vào giỏ hàng.')

    return redirect(request.META.get('HTTP_REFERER', 'snacks:list'))


def update_view(request, snack_id):
    if request.method != 'POST':
        return redirect('cart:detail')

    snack = get_object_or_404(Snack, id=snack_id)
    cart = _get_cart(request)
    item_key = str(snack_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity <= 0:
        cart.pop(item_key, None)
    else:
        cart[item_key] = min(quantity, snack.stock)

    _save_cart(request, cart)
    return redirect('cart:detail')


def remove_view(request, snack_id):
    cart = _get_cart(request)
    cart.pop(str(snack_id), None)
    _save_cart(request, cart)
    return redirect('cart:detail')


def clear_view(request):
    _save_cart(request, {})
    return redirect('cart:detail')
