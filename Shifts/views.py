from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Shift, AssignedShift, ShiftRegistration, User
from .forms import (ShiftForm, ShiftRegistrationForm, AssignShiftForm,)


# ============ QUẢN LÝ CA (OWNER) ============
@login_required
def shift_list(request):
    """Danh sách ca làm việc"""
    if request.user.role not in ['owner', 'staff']:
        messages.error(request, "Bạn không có quyền truy cập")
        return redirect('/accounts/login/')
    
    # Lấy tất cả ca
    shifts = Shift.objects.all().order_by('date', 'start_time')
    
    # Lọc theo ngày
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            date_filter = datetime.strptime(date_filter, '%Y-%m-%d').date()
            shifts = shifts.filter(date=date_filter)
        except ValueError:
            date_filter = None
    
    # Tính tổng đăng ký
    total_registered = 0
    for shift in shifts:
        try:
            shift.registered_count = shift.get_registered_count(date_filter)
            total_registered += shift.registered_count
        except Exception as e:
            shift.registered_count = 0
    
    context = {
        'shifts': shifts,
        'date_filter': date_filter,
        'today': timezone.now().date(),
        'total_registered': total_registered,  # Thêm biến này
        'total_shifts': shifts.count(),        # Thêm biến này
    }
    return render(request, 'shifts/shifts_list.html', context)

@login_required
def shift_create(request):
    """Tạo ca làm việc mới"""
    if request.user.role != 'owner':
        messages.error(request, "Chỉ chủ quán mới có quyền tạo ca")
        return redirect('shifts:shift_list')
    
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tạo ca làm việc thành công")
            return redirect('shifts:shift_list')
    else:
        form = ShiftForm()
    
    return render(request, 'shifts/shift_form.html', {'form': form, 'title': 'Tạo ca mới'})


@login_required
def shift_update(request, pk):
    """Cập nhật ca làm việc"""
    if request.user.role != 'owner':
        messages.error(request, "Chỉ chủ quán mới có quyền chỉnh sửa ca")
        return redirect('shifts:shift_list')
    
    shift = get_object_or_404(Shift, pk=pk)
    
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật ca làm việc thành công")
            return redirect('shifts:shift_list')
    else:
        form = ShiftForm(instance=shift)
    
    return render(request, 'shifts/shift_form.html', {'form': form, 'title': 'Chỉnh sửa ca'})


@login_required
def shift_delete(request, pk):
    """Xóa ca làm việc"""
    if request.user.role != 'owner':
        messages.error(request, "Chỉ chủ quán mới có quyền xóa ca")
        return redirect('shifts:shift_list')
    
    shift = get_object_or_404(Shift, pk=pk)
    
    # Kiểm tra có nhân viên đã đăng ký chưa
    if shift.registrations.exists() or shift.assigned_shifts.exists():
        messages.error(request, "Không thể xóa ca đã có nhân viên đăng ký hoặc phân công")
        return redirect('shifts:shift_list')
    
    if request.method == 'POST':
        shift.delete()
        messages.success(request, "Xóa ca làm việc thành công")
        return redirect('shifts:shift_list')
    
    return render(request, 'shifts/shift_delete.html', {'shift': shift})


@login_required
def shift_detail(request, pk):
    """Chi tiết ca làm việc"""
    if request.user.role not in ['owner', 'staff']:
        messages.error(request, "Bạn không có quyền truy cập")
        return redirect('/accounts/login/')
    
    shift = get_object_or_404(Shift, pk=pk)
    today = timezone.now().date()
    
    # Xử lý date_filter
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            date_filter = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            date_filter = shift.date
    else:
        date_filter = shift.date
    
    # Danh sách nhân viên đã đăng ký
    registrations = ShiftRegistration.objects.filter(
        shift=shift, 
        date=date_filter
    ).select_related('user')
    
    # Danh sách nhân viên đã được phân công
    assigned = AssignedShift.objects.filter(
        shift=shift, 
        date=date_filter
    ).select_related('user')
    
    # Danh sách ID của nhân viên đã phân công (dùng để check trong template)
    assigned_user_ids = [ass.user.id for ass in assigned]
    
    # Tính số chỗ còn lại
    remaining_slots = shift.capacity - assigned.count()
    
    context = {
        'shift': shift,
        'date_filter': date_filter,
        'today': today,
        'registrations': registrations,
        'assigned': assigned,
        'assigned_user_ids': assigned_user_ids,
        'remaining_slots': remaining_slots,
        'duration_hours': shift.get_duration_hours(),
    }
    return render(request, 'shifts/shift_detail.html', context)

# ============ ĐĂNG KÝ CA (STAFF) ============
@login_required
def shift_register(request):
    """Nhân viên đăng ký ca làm việc"""
    if request.user.role != 'staff':
        messages.error(request, "Chỉ nhân viên mới có thể đăng ký ca")
        return redirect('/accounts/dashboard/staff/')
    
    if request.method == 'POST':
        form = ShiftRegistrationForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                registration = form.save(commit=False)
                registration.user = request.user
                registration.save()
                
                # Debug: In ra console
                print(f"DEBUG: Đã đăng ký ca - User: {request.user}, Shift: {registration.shift.name}, Date: {registration.date}")
                
                messages.success(request, f"Đã đăng ký ca {registration.shift.name} vào ngày {registration.date.strftime('%d/%m/%Y')}")
                return redirect('shifts:shift_register')
            except Exception as e:
                messages.error(request, f"Lỗi khi đăng ký: {str(e)}")
                print(f"DEBUG: Lỗi đăng ký - {str(e)}")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = ShiftRegistrationForm(user=request.user)
    
    # Lấy danh sách ca đã đăng ký
    today = timezone.now().date()
    registrations = ShiftRegistration.objects.filter(
        user=request.user,
        date__gte=today
    ).select_related('shift').order_by('date', 'shift__start_time')
    
    # Thêm thuộc tính is_assigned cho mỗi registration
    for reg in registrations:
        reg.is_assigned = reg.is_assigned
    
    context = {
        'form': form,
        'registrations': registrations,
        'today': today,
        'registered': registrations,  # Thêm cho template shift_register.html
    }
    return render(request, 'shifts/shift_register.html', context)

@login_required
def shift_unregister(request, pk):
    """Hủy đăng ký ca"""
    if request.user.role != 'staff':
        messages.error(request, "Chỉ nhân viên mới có thể hủy đăng ký ca")
        return redirect('/accounts/dashboard/staff/')
    
    registration = get_object_or_404(ShiftRegistration, pk=pk, user=request.user)
    
    # Không cho hủy nếu đã được phân công
    if AssignedShift.objects.filter(
        user=request.user,
        shift=registration.shift,
        date=registration.date
    ).exists():
        messages.error(request, "Không thể hủy ca đã được phân công")
        return redirect('shifts:shift_register')
    
    # Không cho hủy nếu quá gần ngày làm (< 24h)
    if registration.date <= timezone.now().date():
        messages.error(request, "Không thể hủy ca trong vòng 24 giờ trước khi làm")
        return redirect('shifts:shift_register')
    
    registration.delete()
    messages.success(request, "Hủy đăng ký ca thành công")
    return redirect('shifts:shift_register')


@login_required
def my_shifts(request):
    """Xem ca làm việc của tôi"""
    if request.user.role != 'staff':
        messages.error(request, "Chỉ nhân viên mới có thể xem ca làm việc")
        return redirect('/accounts/dashboard/staff/')
    
    # Lọc theo tháng
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    if not month or not year:
        today = timezone.now().date()
        month = today.month
        year = today.year
    else:
        month = int(month)
        year = int(year)
    
    # Lấy ca đã được phân công
    assigned_shifts = AssignedShift.objects.filter(
        user=request.user,
        date__month=month,
        date__year=year
    ).select_related('shift').order_by('date', 'shift__start_time')
    
    # Lấy ca đã đăng ký
    registered_shifts = ShiftRegistration.objects.filter(
        user=request.user,
        date__month=month,
        date__year=year
    ).select_related('shift').order_by('date', 'shift__start_time')
    
    context = {
        'assigned_shifts': assigned_shifts,
        'registered_shifts': registered_shifts,
        'month': month,
        'year': year,
    }
    return render(request, 'shifts/my_shifts.html', context)


@login_required
def my_registrations(request):
    """Xem ca đã đăng ký của tôi"""
    if request.user.role != 'staff':
        messages.error(request, "Chỉ nhân viên mới có thể xem ca đã đăng ký")
        return redirect('accounts:staff_dashboard')
    
    today = timezone.now().date()
    registrations = ShiftRegistration.objects.filter(
        user=request.user,
        date__gte=today
    ).select_related('shift').order_by('date', 'shift__start_time')
    
    context = {
        'registrations': registrations,
        'today': today,
    }
    return render(request, 'shifts/my_registrations.html', context)


# ============ PHÂN CÔNG CA (OWNER) ============

@login_required
def assign_shift(request):
    """Phân công ca cho nhân viên"""
    if request.user.role != 'owner':
        messages.error(request, "Chỉ chủ quán mới có quyền phân công ca")
        return redirect('shifts:shift_list')
    
    # Lấy tất cả nhân viên
    all_staff = User.objects.filter(role='staff', is_active=True).order_by('first_name')
    
    if request.method == 'POST':
        shift_id = request.POST.get('shift')
        employee_ids = request.POST.getlist('employees')  # Lấy danh sách nhân viên
        
        if not shift_id or not employee_ids:
            messages.error(request, "Vui lòng chọn ca và nhân viên")
            return redirect('shifts:assign_shift')
        
        try:
            shift = Shift.objects.get(id=shift_id)
            date_value = shift.date
            
            # Kiểm tra số lượng đã phân công
            currently_assigned = AssignedShift.objects.filter(
                shift=shift, 
                date=date_value
            ).count()
            
            available_slots = shift.capacity - currently_assigned
            
            if len(employee_ids) > available_slots:
                messages.error(request, f"Ca chỉ còn {available_slots} chỗ trống")
                return redirect('shifts:assign_shift')
            
            # Phân công cho từng nhân viên
            count = 0
            for emp_id in employee_ids:
                try:
                    employee = User.objects.get(id=emp_id, role='staff')
                    
                    # Kiểm tra đã phân công chưa
                    if not AssignedShift.objects.filter(
                        user=employee, 
                        shift=shift, 
                        date=date_value
                    ).exists():
                        AssignedShift.objects.create(
                            user=employee,
                            shift=shift,
                            date=date_value
                        )
                        count += 1
                except User.DoesNotExist:
                    continue
            
            messages.success(request, f"✅ Đã phân công {count} nhân viên vào ca {shift.name} ngày {date_value.strftime('%d/%m/%Y')}")
            return redirect('shifts:assign_shift')
            
        except Shift.DoesNotExist:
            messages.error(request, "❌ Ca không tồn tại")
            return redirect('shifts:assign_shift')
    
    # Lấy danh sách ca có sẵn (chỉ ca trong tương lai)
    today = timezone.now().date()
    shifts = Shift.objects.filter(date__gte=today).order_by('date', 'start_time')
    
    context = {
        'all_staff': all_staff,
        'shifts': shifts,
    }
    return render(request, 'shifts/assign_form.html', context)

@login_required
def unassign_shift(request, pk):
    """Hủy phân công ca"""
    if request.user.role != 'owner':
        messages.error(request, "Chỉ chủ quán mới có quyền hủy phân công")
        return redirect('shifts:shift_list')
    
    assigned = get_object_or_404(AssignedShift, pk=pk)
    
    # Không cho hủy nếu ca đã qua
    if assigned.date < timezone.now().date():
        messages.error(request, "Không thể hủy phân công ca đã qua")
        return redirect('shifts:shift_detail', pk=assigned.shift.pk)
    
    shift_name = assigned.shift.name
    assigned.delete()
    messages.success(request, f"Đã hủy phân công ca {shift_name}")
    return redirect('shifts:shift_detail', pk=assigned.shift.pk)