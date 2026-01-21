# Reports/models.py
from django.db import models
from django.contrib.auth.models import User

# XÓA CÁC IMPORTS KHÔNG TỒN TẠI:
# from Staff.models import Staff  # XÓA
# from Shifts.models import Shift  # XÓA
# from Products.models import Product, Category  # XÓA

class Bill(models.Model):
    bill_id = models.CharField(max_length=50, unique=True)
    # Thay vì ForeignKey đến Staff, sử dụng CharField hoặc User
    staff_name = models.CharField(max_length=100, blank=True, null=True)
    # Thay vì ForeignKey đến Shift
    shift_name = models.CharField(max_length=100, blank=True, null=True)
    table_number = models.IntegerField()
    customer_count = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Tiền mặt'),
        ('card', 'Thẻ'),
        ('transfer', 'Chuyển khoản'),
        ('momo', 'Momo'),
        ('zalopay', 'ZaloPay')
    ])
    status = models.CharField(max_length=20, choices=[
        ('paid', 'Đã thanh toán'),
        ('pending', 'Chờ thanh toán'),
        ('cancelled', 'Đã hủy')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bill {self.bill_id} - {self.final_amount}"
    
    @property
    def formatted_created_at(self):
        return self.created_at.strftime('%d/%m/%Y %H:%M')

class BillDetail(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='details')
    product_name = models.CharField(max_length=200)
    product_category = models.CharField(max_length=100, default='Đồ uống')
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Tự động tính total_price
        self.total_price = self.product_price * self.quantity
        super().save(*args, **kwargs)

class DailyRevenue(models.Model):
    date = models.DateField(unique=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bills = models.IntegerField(default=0)
    cash_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    digital_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_bill_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Doanh thu hàng ngày"
        verbose_name_plural = "Doanh thu hàng ngày"
    
    def __str__(self):
        return f"Revenue {self.date}: {self.total_revenue}"
    
    def save(self, *args, **kwargs):
        # Tự động tính average_bill_value
        if self.total_bills > 0:
            self.average_bill_value = self.total_revenue / self.total_bills
        super().save(*args, **kwargs)

class InventoryReport(models.Model):
    product_name = models.CharField(max_length=200)
    product_category = models.CharField(max_length=100, default='Đồ uống')
    current_stock = models.IntegerField()
    min_stock = models.IntegerField(default=10)
    status = models.CharField(max_length=20, choices=[
        ('normal', 'Bình thường'),
        ('low', 'Sắp hết'),
        ('out', 'Hết hàng')
    ], default='normal')
    last_updated = models.DateTimeField(auto_now=True)
    report_date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['status', 'product_category', 'product_name']
        verbose_name = "Báo cáo tồn kho"
        verbose_name_plural = "Báo cáo tồn kho"
    
    def __str__(self):
        return f"{self.product_name} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Tự động cập nhật status
        if self.current_stock == 0:
            self.status = 'out'
        elif self.current_stock <= self.min_stock:
            self.status = 'low'
        else:
            self.status = 'normal'
        super().save(*args, **kwargs)