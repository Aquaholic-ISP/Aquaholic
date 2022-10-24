"""Models for Aquaholic"""
import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

KILOGRAM_TO_POUND = 2.20462262185
OUNCES_TO_MILLILITER = 29.5735296


class UserInfo(models.Model):
    """
    UserInfo class for collect user information.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    exercise_time = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    water_amount_per_day = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    first_notification_time = models.TimeField('first notification time', null=True)
    last_notification_time = models.TimeField('last notification time', null=True)
    total_hours = models.DecimalField(max_digits=10, decimal_places=10, null=True)
    water_amount_per_hour = models.DecimalField(max_digits=10, decimal_places=10, null=True)

    def get_water_amount_per_day(self):
        """Calculate amount of water per day."""
        self.water_amount_per_day = ((self.weight * KILOGRAM_TO_POUND * 0.5) + (self.exercise_time / 30) * 12) \
                                    * OUNCES_TO_MILLILITER

    def get_total_hours(self):
        """Calculate total hours from first and last notification time."""
        date = datetime.date(1, 1, 1)
        first_time = datetime.datetime.combine(date, self.first_notification_time)
        last_time = datetime.datetime.combine(date, self.last_notification_time)
        time = last_time - first_time
        self.total_hours = round(time.seconds / 3600)

    def get_water_amount_per_hour(self):
        """Calculate amount of water per hour."""
        self.water_amount_per_hour = self.water_amount_per_day / self.total_hours


class Schedule(models.Model):
    """Schedule class for create notification time."""
    user_info = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=True)
    notification_time = models.DateTimeField('notification time', null=True)
    expected_amount = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    notification_status = models.BooleanField(default=True)

    def change_notification_status(self):
        """Change notification status."""
        if self.notification_status is True:
            self.notification_status = False
        else:
            self.notification_status = True


class Intake(models.Model):
    """Intake class for collect water intake of user per day."""
    user_info = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=True)
    user_drinks_amount = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    intake_date = models.DateTimeField(default=timezone.now)
