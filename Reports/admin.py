# Reports/admin.py
from django.contrib import admin
from .models import Bill, BillDetail, DailyRevenue, InventoryReport

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['bill_id', 'table_number', 'total_amount', 'final_amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['bill_id', 'table_number']

@admin.register(InventoryReport)
class InventoryReportAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'product_category', 'current_stock', 'min_stock', 'status', 'report_date']
    list_filter = ['status', 'product_category']
    search_fields = ['product_name']

admin.site.register(BillDetail)
admin.site.register(DailyRevenue)