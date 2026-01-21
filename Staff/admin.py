from django.contrib import admin
from .models import SalaryConfig, EmployeeSalary, SalaryPayment

@admin.register(SalaryConfig)
class SalaryConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_type', 'hourly_rate', 'shift_rate', 'monthly_salary', 'is_active']
    list_filter = ['payment_type', 'is_active']
    search_fields = ['name']

@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'year', 'total_salary', 'status', 'paid_date']
    list_filter = ['status', 'month', 'year', 'paid_date']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['total_hours', 'total_shifts', 'base_salary', 'overtime_pay', 'total_salary']
    
    def calculate_salary(self, request, queryset):
        for salary in queryset:
            salary.calculate_salary()
            salary.save()
        self.message_user(request, f"Đã tính toán lại lương cho {queryset.count()} bản ghi")
    calculate_salary.short_description = "Tính toán lại lương"

@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ['salary', 'amount', 'payment_method', 'paid_by', 'paid_at']
    list_filter = ['payment_method', 'paid_at']
    search_fields = ['salary__employee__username', 'transaction_id']