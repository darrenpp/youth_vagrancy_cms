from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_record, name='add_record'),
    path('edit/<int:id>/', views.edit_record, name='edit_record'),
    path('delete/<int:id>/', views.delete_record, name='delete_record'),
    path('statistics/', views.statistics, name='statistics'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
]
