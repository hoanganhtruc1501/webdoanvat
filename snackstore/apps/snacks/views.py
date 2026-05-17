from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from .models import Category, Snack
from .forms import CustomUserCreationForm
from orders.models import Order, OrderItem
from datetime import datetime, timedelta
from django.utils import timezone


def snack_list_view(request):
    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    category_slug = request.GET.get('category')

    snacks = Snack.objects.all()
    categories = Category.objects.filter(is_active=True)
    selected_category = None

    # Lưu total_snacks trước khi filter để hiển thị thông tin
    total_snacks = snacks.count()

    if query:
        snacks = snacks.filter(title__icontains=query)
    if min_price:
        snacks = snacks.filter(price__gte=min_price)
    if max_price:
        snacks = snacks.filter(price__lte=max_price)
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        snacks = snacks.filter(category=selected_category)

    # Đếm số sách sau khi filter
    filtered_snacks_count = snacks.count()

    # Pagination với 12 sách mỗi trang (chia hết cho grid)
    paginator = Paginator(snacks.order_by('title'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Tính toán range hiển thị
    start_index = (page_obj.number - 1) * paginator.per_page + 1
    end_index = min(start_index + paginator.per_page - 1, filtered_snacks_count)

    # Tạo URL parameters để giữ filter khi chuyển trang
    filter_params = {}
    if query:
        filter_params['q'] = query
    if min_price:
        filter_params['min_price'] = min_price
    if max_price:
        filter_params['max_price'] = max_price
    if category_slug:
        filter_params['category'] = category_slug

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'total_snacks': total_snacks,
        'filtered_snacks_count': filtered_snacks_count,
        'start_index': start_index,
        'end_index': end_index,
        'filter_params': filter_params,
        'has_filters': bool(query or min_price or max_price or category_slug),
        'page_title': f'Sách - {selected_category.name}' if selected_category else 'Danh Sách Sách',
    }
    return render(request, 'snacks/snack_list.html', context)


def snack_detail_view(request, slug):
    snack = get_object_or_404(Snack, slug=slug)
    
    # Lấy các sản phẩm cùng category (trừ sản phẩm hiện tại)
    related_snacks = []
    if snack.category:
        related_snacks = Snack.objects.filter(
            category=snack.category
        ).exclude(slug=slug)[:6]  # Lấy tối đa 6 sản phẩm liên quan
    
    context = {
        'snack': snack,
        'related_snacks': related_snacks,
        'page_title': snack.title,
    }
    return render(request, 'snacks/snack_detail.html', context)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tạo tài khoản thành công!")
            return redirect('snacks:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'user/register.html', {'form': form})


def logout_view(request):
    """Custom logout view to show success page"""
    logout(request)
    return render(request, 'user/logout.html')


@login_required
def profile_view(request):
    return render(request, 'user/profile.html')


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard_view(request):
    """Trang dashboard admin với thống kê"""
    
    # Thống kê cơ bản
    total_snacks = Snack.objects.count()
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    
    # Thống kê sách
    snacks_in_stock = Snack.objects.filter(stock__gt=0).count()
    snacks_out_of_stock = Snack.objects.filter(stock=0).count()
    
    # Thống kê đơn hàng theo trạng thái
    orders_pending = Order.objects.filter(status='pending').count()
    orders_processing = Order.objects.filter(status='processing').count()
    orders_shipped = Order.objects.filter(status='shipped').count()
    orders_delivered = Order.objects.filter(status='delivered').count()
    orders_cancelled = Order.objects.filter(status='cancelled').count()
    
    # Thống kê doanh thu
    total_revenue = Order.objects.filter(
        status__in=['delivered', 'shipped']
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Thống kê trong 30 ngày qua
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(created_at__gte=thirty_days_ago).count()
    recent_revenue = Order.objects.filter(
        created_at__gte=thirty_days_ago,
        status__in=['delivered', 'shipped']
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Top 5 sách bán chạy
    top_snacks = OrderItem.objects.values('snack__title', 'snack__author').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    # Đơn hàng gần đây (5 đơn mới nhất)
    recent_orders_list = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Thống kê theo danh mục
    categories_stats = Category.objects.annotate(
        snack_count=Count('snacks'),
        sold_count=Sum('snacks__order_items__quantity')
    ).order_by('-snack_count')[:5]
    
    context = {
        # Thống kê tổng quan
        'total_snacks': total_snacks,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_revenue': total_revenue,
        
        # Thống kê sách
        'snacks_in_stock': snacks_in_stock,
        'snacks_out_of_stock': snacks_out_of_stock,
        
        # Thống kê đơn hàng
        'orders_pending': orders_pending,
        'orders_processing': orders_processing,
        'orders_shipped': orders_shipped,
        'orders_delivered': orders_delivered,
        'orders_cancelled': orders_cancelled,
        
        # Thống kê 30 ngày
        'recent_orders': recent_orders,
        'recent_revenue': recent_revenue,
        
        # Chi tiết
        'top_snacks': top_snacks,
        'recent_orders_list': recent_orders_list,
        'categories_stats': categories_stats,
    }
    
    return render(request, 'admin/dashboard.html', context)

