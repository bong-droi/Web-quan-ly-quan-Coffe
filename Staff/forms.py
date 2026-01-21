from django import forms
from .models import SalaryConfig, EmployeeSalary, SalaryPayment
from django.contrib.auth import get_user_model

User = get_user_model()

class SalaryConfigForm(forms.ModelForm):
    class Meta:
        model = SalaryConfig
        fields = ['name', 'payment_type', 'hourly_rate', 'shift_rate', 
                 'monthly_salary', 'overtime_multiplier', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'shift_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'monthly_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '100000'}),
            'overtime_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        
        if payment_type == 'hourly' and not cleaned_data.get('hourly_rate'):
            self.add_error('hourly_rate', 'Vui lòng nhập lương theo giờ')
        elif payment_type == 'shift' and not cleaned_data.get('shift_rate'):
            self.add_error('shift_rate', 'Vui lòng nhập lương theo ca')
        elif payment_type == 'monthly' and not cleaned_data.get('monthly_salary'):
            self.add_error('monthly_salary', 'Vui lòng nhập lương tháng')
        
        return cleaned_data

class EmployeeSalaryForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=User.objects.filter(role='staff'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Nhân viên"
    )
    
    class Meta:
        model = EmployeeSalary
        fields = ['employee', 'salary_config', 'month', 'year', 'bonus', 'deduction', 'notes']
        widgets = {
            'month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020, 'max': 2100}),
            'bonus': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'deduction': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CalculateSalaryForm(forms.Form):
    """Form tính toán lương tự động"""
    month = forms.IntegerField(
        min_value=1, max_value=12,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Tháng"
    )
    year = forms.IntegerField(
        min_value=2020, max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Năm"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('month')
        year = cleaned_data.get('year')
        
        # Kiểm tra tháng/năm hợp lệ
        from datetime import datetime
        try:
            datetime(year, month, 1)
        except ValueError:
            self.add_error('month', 'Tháng/Năm không hợp lệ')
        
        return cleaned_data

class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ['amount', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }