from django.urls import path
from . import views

urlpatterns = [
    # Cấu hình lương (Owner)
    path('salary-config/', views.salary_config_list, name='salary_config_list'),
    path('salary-config/create/', views.salary_config_create, name='salary_config_create'),
    path('salary-config/<int:pk>/update/', views.salary_config_update, name='salary_config_update'),
    path('salary-config/<int:pk>/delete/', views.salary_config_delete, name='salary_config_delete'),
    
    # Tính toán lương (Owner)
    path('salary/calculate/', views.calculate_salary, name='calculate_salary'),
    path('salary/<int:salary_id>/recalculate/', views.calculate_single_salary, name='recalculate_salary'),
    
    # Quản lý bảng lương (Owner)
    path('salary/', views.salary_list, name='salary_list'),
    path('salary/create/', views.salary_create, name='salary_create'),
    path('salary/<int:pk>/', views.salary_detail, name='salary_detail'),
    path('salary/<int:pk>/update/', views.salary_update, name='salary_update'),
    path('salary/<int:salary_id>/pay/', views.make_payment, name='make_payment'),
    
    # Nhân viên xem lương
    path('my-salary/', views.my_salary, name='my_salary'),
    path('my-salary/<int:pk>/', views.my_salary_detail, name='my_salary_detail'),
]