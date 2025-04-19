from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserRegistrationForm, UserProfileForm, ApplianceForm
from .models import UserProfile, Appliance, EnergyConsumption, Achievement, Schedule
import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import random

def home(request):
    return render(request, 'home/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'home/register.html', {'form': form})

@login_required
def dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    appliances = Appliance.objects.filter(user=request.user, is_active=True)
    schedules = Schedule.objects.filter(appliance__user=request.user)
    
    # Calculate total consumption
    total_consumption = sum(appliance.daily_consumption() * 30 for appliance in appliances)
    
    # Prepare data for charts
    appliance_labels = [app.name for app in appliances]
    appliance_consumption = [app.daily_consumption() * 30 for app in appliances]
    
    # Debug logging
    print("Appliance Labels:", appliance_labels)
    print("Appliance Consumption:", appliance_consumption)
    print("Total Consumption:", total_consumption)
    
    # Generate dynamic suggestions based on user's data
    suggestions = []
    
    # Check if consumption is near limit
    if user_profile.monthly_limit:
        limit_percentage = (total_consumption / user_profile.monthly_limit * 100)
        if limit_percentage > 90:
            suggestions.append({
                'title': 'Critical Usage Alert',
                'description': f'You have used {limit_percentage:.1f}% of your monthly limit. Immediate action required.'
            })
    
    # Analyze high-consumption appliances
    if appliances:
        max_consumer = max(appliances, key=lambda x: x.daily_consumption())
        if max_consumer.daily_usage > 6:
            suggestions.append({
                'title': f'High Usage: {max_consumer.name}',
                'description': f'Consider reducing usage time or upgrading to a more efficient model.'
            })
    
    # Season-based suggestions
    if user_profile.season == 'SUMMER' and user_profile.temperature:
        if user_profile.temperature > 25:
            suggestions.append({
                'title': 'Temperature Management',
                'description': 'High temperature detected. Consider using fans instead of AC when possible.'
            })
    elif user_profile.season == 'WINTER' and user_profile.temperature:
        if user_profile.temperature < 18:
            suggestions.append({
                'title': 'Heating Efficiency',
                'description': 'Low temperature detected. Consider using thermal curtains and sealing drafts.'
            })
    
    # Time-based usage suggestions for high-power devices
    high_power_devices = [app for app in appliances if app.power_consumption > 1000]
    if high_power_devices:
        suggestions.append({
            'title': 'Peak Hour Usage',
            'description': f'Schedule {", ".join(app.name for app in high_power_devices)} usage during off-peak hours (10 PM - 6 AM).'
        })
    
    context = {
        'user_profile': user_profile,
        'total_consumption': total_consumption,
        'monthly_limit': user_profile.monthly_limit,
        'appliance_labels': json.dumps(appliance_labels),
        'appliance_consumption': json.dumps(appliance_consumption),
        'limit_percentage': (total_consumption / user_profile.monthly_limit * 100) if user_profile.monthly_limit else 0,
        'suggestions': suggestions,
        'appliances': appliances,
        'schedules': schedules
    }
    
    return render(request, 'home/dashboard.html', context)

@login_required
def appliances(request):
    if request.method == 'POST':
        form = ApplianceForm(request.POST)
        if form.is_valid():
            appliance = form.save(commit=False)
            appliance.user = request.user
            appliance.save()
            messages.success(request, 'Appliance added successfully!')
            return redirect('appliances')
    else:
        form = ApplianceForm()
    
    appliances = Appliance.objects.filter(user=request.user)
    return render(request, 'home/appliances.html', {
        'form': form,
        'appliances': appliances
    })

@login_required
def profile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=user_profile)
    
    achievements = Achievement.objects.filter(user=request.user).order_by('-date_earned')
    return render(request, 'home/profile.html', {
        'form': form,
        'achievements': achievements
    })

@login_required
def toggle_appliance(request, appliance_id):
    appliance = Appliance.objects.get(id=appliance_id, user=request.user)
    appliance.is_active = not appliance.is_active
    appliance.save()
    return redirect('appliances')

@login_required
def predict_consumption(request):
    user_profile = UserProfile.objects.get(user=request.user)
    appliances = Appliance.objects.filter(user=request.user, is_active=True)
    
    # Simple prediction model
    X = np.array([[
        appliance.power_consumption,
        appliance.daily_usage,
        1 if user_profile.season == 'SUMMER' else 0,
        1 if user_profile.season == 'WINTER' else 0,
        user_profile.temperature or 25,
        user_profile.humidity or 50
    ] for appliance in appliances])
    
    if len(X) == 0:
        return redirect('dashboard')
    
    # Train a simple model (in production, this should be pre-trained)
    y = np.array([appliance.daily_consumption() * 30 for appliance in appliances])
    model = LinearRegression()
    model.fit(X, y)
    
    # Save the model
    joblib.dump(model, 'energy_prediction_model.joblib')
    
    # Make prediction
    predicted_consumption = model.predict(X).sum()
    
    # Save consumption record
    EnergyConsumption.objects.create(
        user=request.user,
        total_consumption=sum(appliance.daily_consumption() * 30 for appliance in appliances),
        predicted_consumption=predicted_consumption,
        is_limit_reached=predicted_consumption > user_profile.monthly_limit
    )
    
    messages.info(request, f'Predicted monthly consumption: {predicted_consumption:.2f} kWh')
    return redirect('dashboard')

@csrf_exempt
@require_http_methods(["POST"])
def save_schedule(request):
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['appliance_id', 'start_time', 'end_time', 'days']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Create new schedule
        schedule = Schedule.objects.create(
            appliance_id=data['appliance_id'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            days=','.join(data['days']),
            active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Schedule created successfully',
            'schedule_id': schedule.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def toggle_schedule(request, schedule_id):
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        schedule.active = not schedule.active
        schedule.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Schedule updated successfully',
            'active': schedule.active
        })
    except Schedule.DoesNotExist:
        return JsonResponse({'error': 'Schedule not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def calculate_costs(request):
    try:
        rate = float(request.GET.get('rate', 6.5))  # Default rate in INR per kWh
        period = request.GET.get('period', 'monthly')
        
        # Get consumption data based on period
        base_consumption = 100  # kWh
        period_multipliers = {
            'daily': 1/30,
            'weekly': 7/30,
            'monthly': 1,
            'yearly': 12
        }
        
        consumption = base_consumption * period_multipliers.get(period, 1)
        estimated_cost = consumption * rate
        savings_potential = estimated_cost * 0.15  # Assuming 15% savings potential
        
        return JsonResponse({
            'estimated_cost': round(estimated_cost, 2),
            'savings_potential': round(savings_potential, 2),
            'currency': '₹'  # Indian Rupee symbol
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def environmental_impact(request):
    try:
        # Get total consumption (simplified example)
        total_consumption = 100  # kWh
        
        # Calculate carbon footprint (0.82 kg CO2 per kWh for Indian grid)
        carbon_footprint = total_consumption * 0.82
        carbon_percentage = min((carbon_footprint / 50) * 100, 100)  # Assuming 50kg as max
        
        # Calculate trees equivalent (1 tree absorbs ~21.77 kg CO2 per year)
        trees_equivalent = round(carbon_footprint / 21.77)
        
        return JsonResponse({
            'carbon_footprint': round(carbon_footprint, 2),
            'carbon_percentage': round(carbon_percentage, 2),
            'trees_equivalent': trees_equivalent
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def predictions(request):
    try:
        # Generate historical data for the last 6 months
        months = [(datetime.now() - timedelta(days=30*i)).strftime('%b %Y') for i in range(6)]
        historical_values = [random.uniform(80, 120) for _ in range(6)]
        
        # Generate predictions for the next month
        last_value = historical_values[-1]
        trend = random.choice([-1, 1]) * random.uniform(5, 15)
        next_month = last_value + trend
        
        # Determine trend direction and class
        if trend > 0:
            trend_direction = 'up'
            trend_class = 'text-danger'
            trend_text = 'Increasing'
        else:
            trend_direction = 'down'
            trend_class = 'text-success'
            trend_text = 'Decreasing'
        
        return JsonResponse({
            'history': {
                'labels': months,
                'values': [round(v, 2) for v in historical_values]
            },
            'predictions': {
                'labels': ['Next Month'],
                'values': [round(next_month, 2)]
            },
            'next_month': round(next_month, 2),
            'trend_direction': trend_direction,
            'trend_class': trend_class,
            'trend_text': trend_text
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def add_appliance(request):
    if request.method == 'POST':
        form = ApplianceForm(request.POST)
        if form.is_valid():
            appliance = form.save(commit=False)
            appliance.user = request.user
            appliance.save()
            messages.success(request, 'Appliance added successfully!')
            return redirect('appliances')
    else:
        form = ApplianceForm()
    
    return render(request, 'home/add_appliance.html', {
        'form': form
    })

@login_required
def edit_appliance(request, appliance_id):
    appliance = get_object_or_404(Appliance, id=appliance_id, user=request.user)
    if request.method == 'POST':
        form = ApplianceForm(request.POST, instance=appliance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appliance updated successfully!')
            return redirect('appliances')
    else:
        form = ApplianceForm(instance=appliance)
    
    return render(request, 'home/edit_appliance.html', {
        'form': form,
        'appliance': appliance
    })

@login_required
def delete_appliance(request, appliance_id):
    appliance = get_object_or_404(Appliance, id=appliance_id, user=request.user)
    appliance.delete()
    messages.success(request, 'Appliance deleted successfully!')
    return redirect('appliances')
