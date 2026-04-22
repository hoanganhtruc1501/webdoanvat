from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from books.models import Book

def get_cart(request):
    """Lấy giỏ hàng từ session"""
    return request.session.get('cart', {})

def save_cart(request, cart):
    """Lưu giỏ hàng vào session"""
    request.session['cart'] = cart
    request.session.modified = True

def cart_view(request):
    """Xem giỏ hàng"""
    cart = get_cart(request)
    cart_items = []
    total_price = 0
    total_quantity = 0
    
    for book_id, quantity in cart.items():
        try:
            book = Book.objects.get(id=int(book_id))
            # Sử dụng giá đã giảm thay vì giá gốc
            discounted_price = book.get_discounted_price()
            item_total = discounted_price * quantity
            cart_items.append({
                'book': book,
                'quantity': quantity,
                'item_total': item_total,
                'discounted_price': discounted_price
            })
            total_price += item_total
            total_quantity += quantity
        except Book.DoesNotExist:
            continue
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_quantity': total_quantity,
        'page_title': 'Giỏ hàng của bạn'
    }
    return render(request, 'cart/cart_detail.html', context)

def add_to_cart(request, book_id):
    """Thêm sách vào giỏ hàng"""
    book = get_object_or_404(Book, id=book_id)
    
    if book.stock <= 0:
        messages.error(request, f'Sách "{book.title}" đã hết hàng!')
        return redirect(request.META.get('HTTP_REFERER', 'books:list'))
    
    # Lấy số lượng từ POST request (nếu có), mặc định là 1
    quantity = 1
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1
    
    cart = get_cart(request)
    book_id_str = str(book_id)
    
    if book_id_str in cart:
        # Kiểm tra nếu tăng số lượng có vượt quá tồn kho không
        new_quantity = cart[book_id_str] + quantity
        if new_quantity > book.stock:
            messages.warning(request, f'Chỉ còn {book.stock} cuốn "{book.title}" trong kho!')
            return redirect(request.META.get('HTTP_REFERER', 'books:list'))
        cart[book_id_str] = new_quantity
        if quantity == 1:
            messages.success(request, f'Đã tăng số lượng "{book.title}" trong giỏ hàng!')
        else:
            messages.success(request, f'Đã thêm {quantity} cuốn "{book.title}" vào giỏ hàng!')
    else:
        # Kiểm tra số lượng yêu cầu có vượt quá tồn kho không
        if quantity > book.stock:
            messages.warning(request, f'Chỉ còn {book.stock} cuốn "{book.title}" trong kho!')
            return redirect(request.META.get('HTTP_REFERER', 'books:list'))
        cart[book_id_str] = quantity
        if quantity == 1:
            messages.success(request, f'Đã thêm "{book.title}" vào giỏ hàng!')
        else:
            messages.success(request, f'Đã thêm {quantity} cuốn "{book.title}" vào giỏ hàng!')
    
    save_cart(request, cart)
    return redirect(request.META.get('HTTP_REFERER', 'books:list'))

def update_cart(request, book_id):
    """Cập nhật số lượng sách trong giỏ hàng"""
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            return remove_from_cart(request, book_id)
        
        if quantity > book.stock:
            messages.warning(request, f'Chỉ còn {book.stock} cuốn "{book.title}" trong kho!')
            return redirect('cart:detail')
        
        cart = get_cart(request)
        cart[str(book_id)] = quantity
        save_cart(request, cart)
        
        messages.success(request, f'Đã cập nhật số lượng "{book.title}"!')
    
    return redirect('cart:detail')

def remove_from_cart(request, book_id):
    """Xóa sách khỏi giỏ hàng"""
    book = get_object_or_404(Book, id=book_id)
    cart = get_cart(request)
    book_id_str = str(book_id)
    
    if book_id_str in cart:
        del cart[book_id_str]
        save_cart(request, cart)
        messages.success(request, f'Đã xóa "{book.title}" khỏi giỏ hàng!')
    
    return redirect('cart:detail')

def clear_cart(request):
    """Xóa toàn bộ giỏ hàng"""
    request.session['cart'] = {}
    request.session.modified = True
    messages.success(request, 'Đã xóa toàn bộ giỏ hàng!')
    return redirect('cart:detail')

def get_cart_count(request):
    """Lấy số lượng sản phẩm trong giỏ hàng (dùng cho AJAX)"""
    cart = get_cart(request)
    count = sum(cart.values())
    return JsonResponse({'count': count})


