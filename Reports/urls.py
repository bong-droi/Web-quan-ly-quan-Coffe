# Reports/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    
    path('revenue/', views.revenue_report, name='revenue_report'),


]