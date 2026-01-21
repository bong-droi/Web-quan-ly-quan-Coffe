from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from Shifts.models import Shift  # Import model Shift từ app Shifts

User = get_user_model()

class SalaryConfig(models.Model):
    """Cấu hình lương theo giờ/ca"""
    PAYMENT_TYPES = (
        ('hourly', 'Theo giờ'),
        ('shift', 'Theo ca'),
        ('monthly', 'Cố định tháng'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Tên cấu hình")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='hourly')
    hourly_rate = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0          # giờ công mặc định = 0
    )    
    shift_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Lương/ca (VNĐ)")
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Lương tháng (VNĐ)")
    overtime_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.5, verbose_name="Hệ số OT")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_payment_type_display()})"

class EmployeeSalary(models.Model):
    """Lương của từng nhân viên"""
    STATUS_CHOICES = (
        ('pending', 'Chờ tính toán'),
        ('calculated', 'Đã tính toán'),
        ('reviewed', 'Đã xem xét'),
        ('paid', 'Đã thanh toán'),
    )
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salaries', verbose_name="Nhân viên")
    salary_config = models.ForeignKey(SalaryConfig, on_delete=models.SET_NULL, null=True, verbose_name="Cấu hình lương")
    month = models.IntegerField(verbose_name="Tháng")
    year = models.IntegerField(verbose_name="Năm")
    
    # Thống kê làm việc
    total_shifts = models.IntegerField(default=0, verbose_name="Tổng số ca")
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Tổng giờ làm")
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Giờ OT")
    
    # Tính lương
    base_salary = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=20000,     # 👈 MẶC ĐỊNH 20.000
    )
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Lương OT")
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Thưởng")
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Khấu trừ")
    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Tổng lương")
    
    # Trạng thái
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    paid_date = models.DateField(null=True, blank=True, verbose_name="Ngày thanh toán")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"Lương {self.employee.username} - {self.month}/{self.year}"
    
    def calculate_salary(self, shifts=None):
        """Tính toán lương tự động dựa trên ca làm việc"""
        if not self.salary_config:
            return
        
        # Lấy tất cả ca làm việc trong tháng (nếu không truyền shifts)
        if shifts is None:
            from django.db.models import Sum
            from datetime import datetime
            import calendar
            
            # Lấy ca làm việc đã hoàn thành
            shifts = Shift.objects.filter(
                assigned_to=self.employee,
                start_time__month=self.month,
                start_time__year=self.year,
                status='completed'
            )
        
        # Tính tổng số ca và giờ làm
        total_shifts = shifts.count()
        
        # Tính tổng số giờ làm việc
        total_hours = 0
        for shift in shifts:
            duration = (shift.end_time - shift.start_time).total_seconds() / 3600
            total_hours += duration
        
        # Giả định: Làm quá 8h/ngày tính OT
        overtime_hours = max(total_hours - (22 * 8), 0)  # 22 ngày làm việc/tháng
        
        # Tính lương theo loại thanh toán
        if self.salary_config.payment_type == 'hourly':
            base = total_hours * self.salary_config.hourly_rate
        elif self.salary_config.payment_type == 'shift':
            base = total_shifts * self.salary_config.shift_rate
        else:  # monthly
            base = self.salary_config.monthly_salary
        
        # Tính lương OT
        overtime_pay = overtime_hours * self.salary_config.hourly_rate * self.salary_config.overtime_multiplier
        
        # Cập nhật thông tin
        self.total_shifts = total_shifts
        self.total_hours = round(total_hours, 2)
        self.overtime_hours = round(overtime_hours, 2)
        self.base_salary = round(base, 2)
        self.overtime_pay = round(overtime_pay, 2)
        self.total_salary = round(base + overtime_pay + self.bonus - self.deduction, 2)
        
        if self.status == 'pending':
            self.status = 'calculated'
    
    def mark_as_paid(self):
        """Đánh dấu đã thanh toán"""
        from django.utils import timezone
        self.status = 'paid'
        self.paid_date = timezone.now().date()
        self.save()

class SalaryPayment(models.Model):
    """Lịch sử thanh toán lương"""
    salary = models.ForeignKey(EmployeeSalary, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Số tiền thanh toán")
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Tiền mặt'),
        ('bank', 'Chuyển khoản'),
        ('momo', 'Ví MoMo'),
        ('zalopay', 'ZaloPay'),
    ], default='cash')
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name="Mã giao dịch")
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='salary_payments_made')
    paid_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Thanh toán {self.amount} cho {self.salary}"
    # Thêm ở cuối file Staff/models.py
Salary = EmployeeSalary  # Tạo alias