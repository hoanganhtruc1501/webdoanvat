from django.conf import settings


def cart_context(request):
    session_key = getattr(settings, "CART_SESSION_ID", "cart")
    cart = request.session.get(session_key, {})
    cart_count = sum(cart.values())

    return {
        "cart_count": cart_count,
        "cart_items_exist": cart_count > 0,
    }
