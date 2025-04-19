from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_limit = models.FloatField(default=0)
    season = models.CharField(max_length=10, choices=[
        ('SUMMER', 'Summer'),
        ('WINTER', 'Winter'),
        ('MONSOON', 'Monsoon')
    ])
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    achievement_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Appliance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    power_consumption = models.FloatField()  # in watts
    daily_usage = models.FloatField()  # in hours
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def daily_consumption(self):
        """Calculate daily consumption in kWh"""
        return (self.power_consumption * self.daily_usage) / 1000

class EnergyConsumption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total_consumption = models.FloatField()  # in kWh
    predicted_consumption = models.FloatField()
    is_limit_reached = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s consumption on {self.date}"

class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    date_earned = models.DateTimeField(auto_now_add=True)
    badge_level = models.CharField(max_length=10, choices=[
        ('BRONZE', 'Bronze'),
        ('SILVER', 'Silver'),
        ('GOLD', 'Gold')
    ])

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Schedule(models.Model):
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE, related_name='schedules')
    start_time = models.TimeField()
    end_time = models.TimeField()
    days = models.CharField(max_length=100)  # Comma-separated list of days
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.appliance.name} schedule ({self.start_time} - {self.end_time})"

    class Meta:
        ordering = ['-created_at']
