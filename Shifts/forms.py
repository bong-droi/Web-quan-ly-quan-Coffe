from django import forms
from django.utils import timezone
from .models import Shift, ShiftRegistration, AssignedShift
from django.contrib.auth import get_user_model

User = get_user_model()

class ShiftForm(forms.ModelForm):
    """Form tạo/sửa ca làm việc (cho Owner)"""
    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time', 'date', 'capacity']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: Ca sáng, Ca chiều...'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')
        
        if start_time and end_time:
            if start_time >= end_time:
                self.add_error('end_time', 'Thời gian kết thúc phải sau thời gian bắt đầu')
        
        if date and date < timezone.now().date():
            self.add_error('date', 'Không thể tạo ca trong quá khứ')
        
        return cleaned_data


class ShiftRegistrationForm(forms.ModelForm):
    """Form đăng ký ca (cho Staff)"""
    class Meta:
        model = ShiftRegistration
        fields = ['shift']
        
    def __init__(self, *args, **kwargs):
        # Lấy user từ kwargs
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Lọc chỉ những ca trong tương lai và còn chỗ
        today = timezone.now().date()
        future_shifts = Shift.objects.filter(date__gte=today).order_by('date', 'start_time')
        
        # Filter shifts that still have capacity
        available_shifts = []
        for shift in future_shifts:
            assigned_count = AssignedShift.objects.filter(
                shift=shift, 
                date=shift.date
            ).count()
            if assigned_count < shift.capacity:
                # Check if user already registered for this shift
                if not ShiftRegistration.objects.filter(
                    user=self.user,
                    shift=shift,
                    date=shift.date
                ).exists():
                    available_shifts.append(shift.id)
        
        self.fields['shift'].queryset = Shift.objects.filter(
            id__in=available_shifts
        )
        
        # Customize label
        self.fields['shift'].label_from_instance = lambda obj: f"{obj.name} - {obj.date.strftime('%d/%m/%Y')} ({obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')})"
    
    def clean(self):
        cleaned_data = super().clean()
        shift = cleaned_data.get('shift')
        
        if shift and self.user:
            # Kiểm tra đã đăng ký chưa
            if ShiftRegistration.objects.filter(
                user=self.user,
                shift=shift,
                date=shift.date
            ).exists():
                raise forms.ValidationError('Bạn đã đăng ký ca này rồi')
            
            # Kiểm tra còn chỗ không
            assigned_count = AssignedShift.objects.filter(
                shift=shift,
                date=shift.date
            ).count()
            
            if assigned_count >= shift.capacity:
                raise forms.ValidationError('Ca này đã đủ người')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
            instance.date = instance.shift.date  # Lấy ngày từ shift
        
        if commit:
            instance.save()
        
        return instance

class AssignShiftForm(forms.Form):
    """Form phân công ca (cho Owner)"""
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.filter(date__gte=timezone.now().date()),
        label="Chọn ca",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'shiftSelect'
        })
    )
    
    employees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='staff', is_active=True),
        label="Chọn nhân viên",
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 5,
            'id': 'employeeSelect'
        }),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tùy chỉnh label để hiển thị ngày
        self.fields['shift'].label_from_instance = lambda obj: f"{obj.name} - {obj.date.strftime('%d/%m/%Y')} ({obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')})"
        
        