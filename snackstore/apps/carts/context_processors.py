def cart_context(request):
    """Context processor để cung cấp thông tin giỏ hàng cho tất cả templates"""
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    
    return {
        'cart_count': cart_count,
        'cart_items_exist': cart_count > 0
    } 
