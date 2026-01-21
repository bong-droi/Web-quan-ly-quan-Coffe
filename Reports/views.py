# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.db.models import Count, Sum, Q, Avg, F
# from django.utils import timezone
# from datetime import datetime, timedelta

# from flask import redirect
# from Shifts.models import Shift, ShiftRegistration, AssignedShift
# from orders.models import Order 

# @login_required
# def dashboard(request):
#     """Dashboard báo cáo đơn giản"""
#     # Lấy dữ liệu từ model Order
#     try:
#         orders = Order.objects.all()
        
#         # Hôm nay
#         today = timezone.now().date()
#         today_orders = orders.filter(created_at__date=today)
        
#         # Tính toán
#         today_revenue = today_orders.aggregate(
#             total=Sum('total_amount')
#         )['total'] or 0
        
#         today_bills = today_orders.count()
        
#         total_revenue = orders.aggregate(
#             total=Sum('total_amount')
#         )['total'] or 0
        
#         total_bills = orders.count()
        
#     except Exception as e:
#         # Nếu không có dữ liệu
#         today_revenue = 0
#         today_bills = 0
#         total_revenue = 0
#         total_bills = 0
    
#     context = {
#         'today_revenue': today_revenue,
#         'today_bills': today_bills,
#         'total_revenue': total_revenue,
#         'total_bills': total_bills,
#     }
    
#     return render(request, 'reports/dashboard.html', context)


# @login_required
# def revenue_report(request):
#     """Báo cáo doanh thu và bill theo khoảng thời gian"""
    
#     # Mặc định: hôm nay
#     end_date = timezone.now().date()
#     start_date = end_date
    
#     # Lấy tham số từ URL nếu có
#     start_date_str = request.GET.get('start_date')
#     end_date_str = request.GET.get('end_date')
    
#     if start_date_str:
#         try:
#             start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#         except:
#             start_date = timezone.now().date()
    
#     if end_date_str:
#         try:
#             end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
#         except:
#             end_date = timezone.now().date()
    
#     # Đảm bảo start_date <= end_date
#     if start_date > end_date:
#         start_date, end_date = end_date, start_date
    
#     try:
#         # Lọc đơn hàng theo khoảng thời gian
#         orders = Order.objects.filter(
#             created_at__date__gte=start_date,
#             created_at__date__lte=end_date
#         ).order_by('-created_at')
        
#         # Tính toán thống kê
#         total_revenue = orders.aggregate(
#             total=Sum('total_amount')
#         )['total'] or 0
        
#         total_bills = orders.count()
        
#         # Thống kê theo loại (nếu model có trường type hoặc customer/staff)
#         customer_orders = orders.filter(customer__isnull=False)
#         staff_orders = orders.filter(staff__isnull=False)
        
#         customer_revenue = customer_orders.aggregate(
#             total=Sum('total_amount')
#         )['total'] or 0
        
#         staff_revenue = staff_orders.aggregate(
#             total=Sum('total_amount')
#         )['total'] or 0
        
#         context = {
#             'orders': orders,
#             'total_revenue': total_revenue,
#             'total_bills': total_bills,
#             'customer_revenue': customer_revenue,
#             'staff_revenue': staff_revenue,
#             'customer_count': customer_orders.count(),
#             'staff_count': staff_orders.count(),
#             'start_date': start_date,
#             'end_date': end_date,
#             'date_range': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
#         }
        
#     except Exception as e:
#         # Nếu không có dữ liệu hoặc lỗi
#         context = {
#             'orders': [],
#             'total_revenue': 0,
#             'total_bills': 0,
#             'start_date': start_date,
#             'end_date': end_date,
#             'date_range': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
#             'error': str(e)
#         }
    
#     return render(request, 'reports/revenue_report.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta

# SỬA LẠI: Import đúng models từ app Reports
from .models import Bill, DailyRevenue, InventoryReport

@login_required
def dashboard(request):
    """Dashboard báo cáo đơn giản"""
    # SỬA: Sử dụng model Bill thay vì Order
    try:
        bills = Bill.objects.all()
        
        # Hôm nay
        today = timezone.now().date()
        today_bills = bills.filter(created_at__date=today)
        
        # Tính toán
        today_revenue = today_bills.aggregate(
            total=Sum('final_amount')
        )['total'] or 0
        
        today_bills_count = today_bills.count()
        
        total_revenue = bills.aggregate(
            total=Sum('final_amount')
        )['total'] or 0
        
        total_bills_count = bills.count()
        
    except Exception as e:
        today_revenue = 0
        today_bills_count = 0
        total_revenue = 0
        total_bills_count = 0
    
    context = {
        'today_revenue': today_revenue,
        'today_bills': today_bills_count,
        'total_revenue': total_revenue,
        'total_bills': total_bills_count,
        'today': timezone.now().date(),
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
def revenue_report(request):
    """Báo cáo doanh thu và bill theo khoảng thời gian"""
    
    # Mặc định: hôm nay
    end_date = timezone.now().date()
    start_date = end_date
    
    # Lấy tham số từ URL nếu có
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except:
            start_date = timezone.now().date()
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except:
            end_date = timezone.now().date()
    
    # Đảm bảo start_date <= end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    try:
        # SỬA: Sử dụng model Bill thay vì Order
        bills = Bill.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).order_by('-created_at')
        
        # Tính toán thống kê
        total_revenue = bills.aggregate(
            total=Sum('final_amount')
        )['total'] or 0
        
        total_bills_count = bills.count()
        
        # Thống kê theo phương thức thanh toán
        cash_amount = bills.filter(payment_method='cash').aggregate(
            total=Sum('final_amount')
        )['total'] or 0
        
        card_amount = bills.filter(payment_method='card').aggregate(
            total=Sum('final_amount')
        )['total'] or 0
        
        # Tính trung bình
        average_bill = total_revenue / total_bills_count if total_bills_count > 0 else 0
        
        context = {
            'bills': bills,  # SỬA: Đổi từ 'orders' thành 'bills'
            'total_revenue': total_revenue,
            'total_bills': total_bills_count,
            'cash_amount': cash_amount,
            'card_amount': card_amount,
            'average_bill': average_bill,
            'start_date': start_date,
            'end_date': end_date,
            'date_range': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
        }
        
    except Exception as e:
        context = {
            'bills': [],  # SỬA: Đổi từ 'orders' thành 'bills'
            'total_revenue': 0,
            'total_bills': 0,
            'start_date': start_date,
            'end_date': end_date,
            'date_range': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            'error': str(e)
        }
    
    return render(request, 'reports/revenue_report.html', context)