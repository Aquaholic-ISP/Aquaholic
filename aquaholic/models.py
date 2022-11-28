"""Models for Aquaholic application."""
import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

KILOGRAM_TO_POUND = 2.20462262185
OUNCES_TO_MILLILITER = 29.5735296


class UserInfo(models.Model):
    """UserInfo class for collect user information."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    weight = models.FloatField(default=0)
    exercise_duration = models.FloatField(default=0)
    water_amount_per_day = models.IntegerField(default=0)
    first_notification_time = models.TimeField('first notification time', default=datetime.time(8, 0, 0))
    last_notification_time = models.TimeField('last notification time', default=datetime.time(22, 0, 0))
    total_hours = models.FloatField(null=True)
    water_amount_per_hour = models.IntegerField(null=True)
    notify_token = models.CharField(max_length=200, null=True)
    time_interval = models.IntegerField(default=1)
    notification_turned_on = models.BooleanField(default=True)

    def set_water_amount_per_day(self):
        """Calculate amount of water per day."""
        self.water_amount_per_day = int(((self.weight * KILOGRAM_TO_POUND * 0.5) + (self.exercise_duration / 30) * 12) * OUNCES_TO_MILLILITER)

    def set_water_amount_per_hour(self):
        """Calculate amount of water per hour."""
        if self.total_hours is not None:
            num_notifications = int(self.total_hours/self.time_interval) + 1  # include last
            self.water_amount_per_hour = int(self.water_amount_per_day / num_notifications)


class Schedule(models.Model):
    """Schedule class for create notification time."""

    user_info = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=True)
    notification_time = models.DateTimeField('notification time', null=True)
    expected_amount = models.IntegerField(default=0)
    notification_status = models.BooleanField(default=True)
    is_last = models.BooleanField(default=False)


class Intake(models.Model):
    """Intake class for collect water intake of user per day."""

    user_info = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=True)
    total_amount = models.FloatField(default=0)
    date = models.DateTimeField(default=timezone.now)
