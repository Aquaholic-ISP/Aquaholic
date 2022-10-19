"""Models for Aquaholic"""
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

KILOGRAM_TO_POUND = 2.20462262185
OUNCES_TO_MILLILITER = 29.5735296


class UserInfo(models.Model):
    """
    UserInfo class for collect user information.
    """
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    exercise_time = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    water_amount_per_day = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    first_notification_time = models.DateTimeField('first notification time', null=True)
    last_notification_time = models.DateTimeField('last notification time', null=True)
    total_awake_time = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    water_amount_per_hour = models.DecimalField(max_digits=10, decimal_places=10, default=0)

    def get_water_amount(self):
        amount = ((self.weight * KILOGRAM_TO_POUND * 0.5) + (self.exercise_time / 30) * 12) * OUNCES_TO_MILLILITER
        return amount

    def get_total_awake_time(self):
        pass

    def get_water_amount_in_each_hour(self):
        pass


class Schedule(models.Model):
    # user_info = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # notification_time = models.DateTimeField('notification time')
    # expected_amount = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    # notification_status = models.BooleanField(default=True)
    pass

    # def set_notification_status(self):
    #     pass


class Intake(models.Model):
    # user_info = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # user_drinks_amount = models.DecimalField(max_digits=10, decimal_places=10, default=0)
    # intake_date = models.DateTimeField(default=timezone.now)
    pass
