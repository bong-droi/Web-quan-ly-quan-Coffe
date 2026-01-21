from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Chủ quán'),
        ('staff', 'Nhân viên'),
        ('customer', 'Khách hàng'),   # 👉 thêm role khách hàng
    )

    role = models.CharField(max_length=20, default="customer")

    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.username} ({self.role})"

