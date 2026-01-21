from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime
import calendar
from decimal import Decimal

from .models import Salary, SalaryConfig, EmployeeSalary, SalaryPayment
from .forms import SalaryConfigForm, EmployeeSalaryForm, CalculateSalaryForm, SalaryPaymentForm
from Shifts.models import AssignedShift, Shift

User = get_user_model()

def is_owner(user):
    return user.role == 'owner' or user.is_staff

# ========== QUẢN LÝ CẤU HÌNH LƯƠNG ==========

@login_required
@user_passes_test(is_owner)
def salary_config_list(request):
    configs = SalaryConfig.objects.all()
    return render(request, 'Staff/salary_config_list.html', {'configs': configs})

@login_required
@user_passes_test(is_owner)
def salary_config_create(request):
    if request.method == 'POST':
        form = SalaryConfigForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã tạo cấu hình lương mới!')
            return redirect('salary_config_list')
    else:
        form = SalaryConfigForm()
    return render(request, 'Staff/salary_form.html', {'form': form, 'title': 'Tạo cấu hình lương'})

@login_required
@user_passes_test(is_owner)
def salary_config_update(request, pk):
    config = get_object_or_404(SalaryConfig, pk=pk)
    if request.method == 'POST':
        form = SalaryConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật cấu hình lương!')
            return redirect('salary_config_list')
    else:
        form = SalaryConfigForm(instance=config)
    return render(request, 'Staff/salary_form.html', {'form': form, 'title': 'Sửa cấu hình lương'})

@login_required
@user_passes_test(is_owner)
def salary_config_delete(request, pk):
    config = get_object_or_404(SalaryConfig, pk=pk)
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Đã xóa cấu hình lương!')
        return redirect('salary_config_list')
    return render(request, 'Staff/salary_confirm_delete.html', {'config': config})

# ========== TÍNH TOÁN LƯƠNG ==========

@login_required
@user_passes_test(is_owner)
def calculate_single_salary(request, salary_id):
    """Tính toán lại lương cho một nhân viên cụ thể"""
    salary = get_object_or_404(EmployeeSalary, pk=salary_id)
    
    # Lấy ca làm việc
    shifts = Shift.objects.filter(
        assigned_to=salary.employee,
        start_time__month=salary.month,
        start_time__year=salary.year,
        status='completed'
    )
    
    # Tính toán lại
    salary.calculate_salary(shifts)
    salary.save()
    
    messages.success(request, f'Đã tính toán lại lương cho {salary.employee.get_full_name()}')
    return redirect('salary_detail', pk=salary_id)

# ========== QUẢN LÝ BẢNG LƯƠNG ==========

@login_required
@user_passes_test(is_owner)
def calculate_salary(request):
    if request.method == "POST":
        month = int(request.POST.get("month"))
        year = int(request.POST.get("year"))

        employees = User.objects.filter(role="staff")

        for emp in employees:

            # LẤY CA LÀM
            assignments = AssignedShift.objects.filter(
                user=emp,
                shift__date__month=month,
                shift__date__year=year
            )

            if not assignments.exists():
                continue

            total_hours = 0
            total_shifts = assignments.count()

            for a in assignments:
                start = a.shift.start_time
                end = a.shift.end_time
                duration = (
                    datetime.combine(a.shift.date, end)
                    - datetime.combine(a.shift.date, start)
                ).seconds / 3600
                total_hours += duration

            # Lương cơ bản MẶC ĐỊNH = 20.000
            base_salary = Decimal(20000)

            # TÍNH LƯƠNG
            hourly_rate = Decimal(20000)    # 20.000đ / giờ

            total_salary = Decimal(total_hours) * hourly_rate

            EmployeeSalary.objects.update_or_create(
                employee=emp,
                month=month,
                year=year,
                defaults={
                    "total_hours": total_hours,
                    "total_shifts": total_shifts,
                    "base_salary": hourly_rate,
                    "total_salary": total_salary,
                    "status": "calculated"
                }
            )


        messages.success(request, "Tính lương thành công!")
        return redirect("salary_list")

    return render(request, "Staff/calculate_salary.html", {
        "months": range(1, 13),
        "years": range(2020, 2031),
    })


@login_required
@user_passes_test(is_owner)
def salary_detail(request, pk):
    """Chi tiết bảng lương"""
    salary = get_object_or_404(EmployeeSalary, pk=pk)
    
    # Lấy ca làm việc trong tháng
    shifts = Shift.objects.filter(
        assigned_to=salary.employee,
        start_time__month=salary.month,
        start_time__year=salary.year,
        status='completed'
    ).order_by('start_time')
    
    # Lấy lịch sử thanh toán
    payments = salary.payments.all()
    
    # Form thanh toán
    payment_form = SalaryPaymentForm()
    
    return render(request, 'Staff/salary_detail.html', {
        'salary': salary,
        'shifts': shifts,
        'payments': payments,
        'payment_form': payment_form,
    })

@login_required
@user_passes_test(is_owner)
def salary_create(request):
    """Tạo bảng lương thủ công"""
    if request.method == 'POST':
        form = EmployeeSalaryForm(request.POST)
        if form.is_valid():
            salary = form.save(commit=False)
            
            # Tính toán lương tự động
            salary.calculate_salary()
            salary.save()
            
            messages.success(request, 'Đã tạo bảng lương!')
            return redirect('salary_detail', pk=salary.pk)
    else:
        form = EmployeeSalaryForm()
    
    return render(request, 'Staff/salary_form.html', {
        'form': form,
        'title': 'Tạo bảng lương'
    })

@login_required
@user_passes_test(is_owner)
def salary_update(request, pk):
    """Cập nhật bảng lương"""
    salary = get_object_or_404(EmployeeSalary, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeSalaryForm(request.POST, instance=salary)
        if form.is_valid():
            salary = form.save()
            # Tính toán lại tổng lương
            salary.total_salary = salary.base_salary + salary.overtime_pay + salary.bonus - salary.deduction
            salary.save()
            
            messages.success(request, 'Đã cập nhật bảng lương!')
            return redirect('salary_detail', pk=salary.pk)
    else:
        form = EmployeeSalaryForm(instance=salary)
    
    return render(request, 'Staff/salary_form.html', {
        'form': form,
        'title': 'Sửa bảng lương',
        'salary': salary
    })

@login_required
@user_passes_test(is_owner)
def make_payment(request, salary_id):
    """Thanh toán lương"""
    salary = get_object_or_404(EmployeeSalary, pk=salary_id)
    
    if request.method == 'POST':
        form = SalaryPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.salary = salary
            payment.paid_by = request.user
            payment.save()
            
            # Cập nhật trạng thái lương
            salary.mark_as_paid()
            
            messages.success(request, f'Đã thanh toán {payment.amount:,.0f} VNĐ')
            return redirect('salary_detail', pk=salary_id)
    
    return redirect('salary_detail', pk=salary_id)

# ========== NHÂN VIÊN XEM LƯƠNG ==========

@login_required
def my_salary(request):
    """Nhân viên xem lương của mình"""
    employee = request.user
    salaries = EmployeeSalary.objects.filter(employee=employee).order_by('-year', '-month')
    
    # Tổng kết
    total_earned = salaries.aggregate(total=Sum('total_salary'))['total'] or 0
    paid_salaries = salaries.filter(status='paid').count()
    
    return render(request, 'Staff/my_salary.html', {
        'salaries': salaries,
        'total_earned': total_earned,
        'paid_salaries': paid_salaries,
        'employee': employee,
    })

@login_required
def my_salary_detail(request, pk):
    """Nhân viên xem chi tiết lương"""
    salary = get_object_or_404(EmployeeSalary, pk=pk, employee=request.user)
    
    # Lấy ca làm việc
    shifts = Shift.objects.filter(
        assigned_to=request.user,
        start_time__month=salary.month,
        start_time__year=salary.year,
        status='completed'
    ).order_by('start_time')
    
    return render(request, 'Staff/my_salary_detail.html', {
        'salary': salary,
        'shifts': shifts,
    })
    
@login_required
@user_passes_test(is_owner)
def salary_list(request):
    salaries = EmployeeSalary.objects.all().select_related('employee', 'salary_config')

    month = request.GET.get('month')
    year = request.GET.get('year')

    if month and year:
        salaries = salaries.filter(month=month, year=year)

    total_salary = salaries.aggregate(total=Sum('total_salary'))['total'] or 0
    total_employees = salaries.values('employee').distinct().count()

    months = list(range(1, 12 + 1))
    years = range(2020, 2035)

    return render(request, 'Staff/salary_list.html', {
        'salaries': salaries,
        'total_salary': total_salary,
        'total_employees': total_employees,
        'months': months,
        'years': years
    })
