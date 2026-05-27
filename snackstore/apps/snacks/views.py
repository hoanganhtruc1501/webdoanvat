from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Category, HomeComment, Snack
from .forms import CustomUserCreationForm, HomeCommentForm, ReviewForm
from orders.models import Order, OrderItem
from datetime import datetime, timedelta
from django.utils import timezone


def snack_list_view(request):
    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    category_slug = request.GET.get('category')
    home_comment_form = HomeCommentForm()
    editing_comment = None

    if request.method == 'POST':
        action = request.POST.get("action")
        if action in {"create", "update", "delete"}:
            if not request.user.is_authenticated:
                return redirect(f"{reverse('snacks:login')}?next={request.path}")

            if action == "delete":
                home_comment = HomeComment.objects.filter(
                    pk=request.POST.get("comment_id"),
                    user=request.user,
                ).first()
                if home_comment:
                    home_comment.delete()
                    messages.success(request, "Comment đã được xoá.")
                else:
                    messages.error(request, "Bạn không có quyền xoá comment này.")
                return redirect('snacks:list')

            if action == "update":
                editing_comment = HomeComment.objects.filter(
                    pk=request.POST.get("comment_id"),
                    user=request.user,
                ).first()
                if not editing_comment:
                    messages.error(request, "Bạn không có quyền sửa comment này.")
                    return redirect('snacks:list')
                home_comment_form = HomeCommentForm(request.POST, instance=editing_comment)
            else:
                home_comment_form = HomeCommentForm(request.POST)

            if home_comment_form.is_valid():
                home_comment = home_comment_form.save(commit=False)
                home_comment.user = request.user
                home_comment.is_active = True
                home_comment.save()
                messages.success(request, "Comment đã được lưu.")
                return redirect('snacks:list')
    else:
        edit_comment_id = request.GET.get("edit_comment")
        if request.user.is_authenticated and edit_comment_id:
            editing_comment = HomeComment.objects.filter(
                pk=edit_comment_id,
                user=request.user,
            ).first()
            if editing_comment:
                home_comment_form = HomeCommentForm(instance=editing_comment)

    snacks = Snack.objects.all()
    categories = Category.objects.filter(is_active=True)
    selected_category = None
    home_comments = HomeComment.objects.filter(is_active=True).select_related("user")

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
        'home_comment_form': home_comment_form,
        'home_comments': home_comments,
        'editing_comment': editing_comment,
        'total_snacks': total_snacks,
        'filtered_snacks_count': filtered_snacks_count,
        'start_index': start_index,
        'end_index': end_index,
        'filter_params': filter_params,
        'has_filters': bool(query or min_price or max_price or category_slug),
        'page_title': f'Sản phẩm - {selected_category.name}' if selected_category else 'Danh sách sản phẩm',
    }
    return render(request, 'snacks/snack_list.html', context)


def snack_detail_view(request, slug):
    snack = get_object_or_404(Snack, slug=slug)
    reviews = snack.reviews.filter(is_active=True).select_related('user')
    user_review = None

    if request.user.is_authenticated:
        user_review = snack.reviews.filter(user=request.user).first()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, "Bạn cần đăng nhập để đánh giá sản phẩm.")
            return redirect(f"/login/?next={request.path}")

        review_form = ReviewForm(request.POST, instance=user_review)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.snack = snack
            review.user = request.user
            review.is_active = True
            review.save()
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá sản phẩm.")
            return redirect('snacks:detail', slug=snack.slug)
    else:
        review_form = ReviewForm(instance=user_review)
    
    # Lấy các sản phẩm cùng category (trừ sản phẩm hiện tại)
    related_snacks = []
    if snack.category:
        related_snacks = Snack.objects.filter(
            category=snack.category
        ).exclude(slug=slug)[:6]  # Lấy tối đa 6 sản phẩm liên quan
    
    context = {
        'snack': snack,
        'related_snacks': related_snacks,
        'reviews': reviews,
        'review_form': review_form,
        'user_review': user_review,
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
    orders_shipped = Order.objects.filter(status='shipping').count()
    orders_delivered = Order.objects.filter(status='completed').count()
    orders_cancelled = Order.objects.filter(status='cancelled').count()
    
    # Thống kê doanh thu
    completed_orders = Order.objects.filter(status='completed')
    total_revenue = sum((order.final_total for order in completed_orders), Decimal('0'))
    
    # Thống kê trong 30 ngày qua
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(created_at__gte=thirty_days_ago).count()
    recent_completed_orders = Order.objects.filter(
        created_at__gte=thirty_days_ago,
        status='completed'
    )
    recent_revenue = sum((order.final_total for order in recent_completed_orders), Decimal('0'))
    
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
    
    return render(request, 'admin/dashboard.html', context)
