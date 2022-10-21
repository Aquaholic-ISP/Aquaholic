import datetime
from django.test import TestCase
from django.utils import timezone
from aquaholic.models import UserInfo
from django.urls import reverse
from django.contrib.auth.models import User
from http import HTTPStatus


def create_userinfo(weight, exercise_time, first_notification_time, last_notification_time):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    return UserInfo(weight=weight, exercise_time=exercise_time, first_notification_time=first_notification_time,
                    last_notification_time=last_notification_time)


class UserInfoModelTests(TestCase):
    def test_amount_of_water(self):
        """calculate the amount of water from user input weight
        and exercise time."""
        user = UserInfo(weight=50, exercise_time=60)
        user.get_water_amount_per_day()
        amount = 2339.7265
        self.assertAlmostEqual(amount, user.water_amount_per_day, places=4)

    def test_get_total_hour(self):
        """calculate the total hour from user input notification time."""
        user = create_userinfo(50, 60, first_notification_time=datetime.time(8, 0, 0), last_notification_time=datetime.time(22, 0, 0))
        user.get_total_hours()
        total = 14
        self.assertEqual(total, user.total_hours)

    def test_amount_per_hour(self):
        """calculate the amount of water user to intake per hour."""
        user = create_userinfo(50, 60, first_notification_time=datetime.time(8, 0, 0),
                               last_notification_time=datetime.time(22, 0, 0))
        per_hour = 167.1233227
        user.get_water_amount_per_day()
        user.get_total_hours()
        user.get_water_amount_per_hour()
        self.assertAlmostEqual(per_hour, user.water_amount_per_hour, 5)


class HomePageView(TestCase):
    def test_home_page(self):
        """redirect to homepage view to calculate water intake"""
        response = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_calculate_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        cal_url = reverse('aquaholic:home')
        self.assertEqual(response.url, cal_url)


class CalculateView(TestCase):
    def test_calculate_page(self):
        """redirect to calculate page to calculate water intake"""
        response = self.client.get(reverse('aquaholic:calculate'))
        self.assertEqual(response.status_code, 200)

    def test_invalid_input(self):
        """input invalid value"""
        response = self.client.post('/aquaholic/calculate', data={"weight": "weight", "exercise_time": 0})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Please, enter a positive number in both fields.", html=True)



