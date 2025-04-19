from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('appliances/', views.appliances, name='appliances'),
    path('profile/', views.profile, name='profile'),
    path('appliance/toggle/<int:appliance_id>/', views.toggle_appliance, name='toggle_appliance'),
    path('predict/', views.predict_consumption, name='predict_consumption'),
    path('appliances/add/', views.add_appliance, name='add_appliance'),
    path('appliances/<int:appliance_id>/edit/', views.edit_appliance, name='edit_appliance'),
    path('appliances/<int:appliance_id>/delete/', views.delete_appliance, name='delete_appliance'),
    
    # API endpoints
    path('api/schedules/', views.save_schedule, name='save_schedule'),
    path('api/schedules/<int:schedule_id>/toggle/', views.toggle_schedule, name='toggle_schedule'),
    path('api/calculate-costs/', views.calculate_costs, name='calculate_costs'),
    path('api/environmental-impact/', views.environmental_impact, name='environmental_impact'),
    path('api/predictions/', views.predictions, name='predictions'),
] 