from django.test import TestCase

# Create your tests here.
import datetime
from aquaholic.models import UserInfo
from django.urls import reverse
from http import HTTPStatus
from django.test import TestCase
from aquaholic.views import *
from django.contrib.auth.models import User
from urllib import request


def create_userinfo(weight, exercise_time, first_notification_time, last_notification_time):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    return UserInfo.objects.create(weight=weight, exercise_time=exercise_time, first_notification_time=first_notification_time,
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
        user = create_userinfo(50, 60, first_notification_time=datetime.time(8, 0, 0),
                               last_notification_time=datetime.time(22, 0, 0))
        user.total_hours = get_total_hours(user.first_notification_time, user.last_notification_time)
        total = 14
        self.assertEqual(total, user.total_hours)

    def test_amount_per_hour(self):
        """calculate the amount of water user to intake per hour."""
        user = create_userinfo(50, 60, first_notification_time=datetime.time(8, 0, 0),
                               last_notification_time=datetime.time(22, 0, 0))
        per_hour = 167.1233227
        user.get_water_amount_per_day()
        user.total_hours = get_total_hours(user.first_notification_time, user.last_notification_time)
        user.get_water_amount_per_hour()
        self.assertAlmostEqual(per_hour, user.water_amount_per_hour, 5)


class HomePageView(TestCase):
    def test_home_page(self):
        """redirect to homepage view to calculate water intake"""
        response = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_home_page(self):
        """client redirect to home page"""
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


class TemplateUsed(TestCase):
    def test_template_used(self):
        """template used correctly"""
        response = self.client.get(reverse('aquaholic:calculate'))
        self.assertTemplateUsed(response, 'aquaholic/calculate.html')
        response = self.client.get(reverse('aquaholic:home'))
        self.assertTemplateUsed(response, 'aquaholic/home.html')
        self.client.login()
        cal_url = self.client.get(reverse('aquaholic:home'))
        self.assertTemplateUsed(cal_url, 'aquaholic/home.html')
        first_notify_time = datetime.time(10, 0, 0)
        last_notify_time = datetime.time(22, 0, 0)
        user = create_userinfo(80, 0, first_notify_time, last_notify_time)
        userinfo = User.objects.filter(id=user.id)
        setup_url = self.client.get(reverse('aquaholic:set_up', args=(userinfo,)))
        self.assertTemplateUsed(setup_url, 'aquaholic/set_up.html')
        # schedule_url = self.client.get(reverse('aquaholic:schedule'))
        # self.assertTemplateUsed(schedule_url, 'aquaholic/schedule.html')


class LoginWithLine(TestCase):
    def test_authenticated_using_line(self):
        """After login redirect to calculation page"""
        self.client.login()
        cal_url = reverse('aquaholic:home')
        response = self.client.get(cal_url)
        self.assertEqual(response.status_code, 200)


class SetUpView(TestCase):
    # def test_setup_page(self):
    #     page = self.client.get(reverse('aquaholic:set_up'))
    #     self.assertEqual(page.status_code, 200)

    def test_get_notification_time(self):
        first_notify_time = datetime.time.strftime(datetime.time(10, 0, 0), "%H:%M")
        last_notify_time = datetime.time.strftime(datetime.time(22, 0, 0), "%H:%M")

        self.client.login()
        user = create_userinfo(80, 0, first_notify_time, last_notify_time)
        self.assertEqual(user.first_notification_time, "10:00")
        self.assertEqual(user.last_notification_time, "22:00")


class ScheduleView(TestCase):
    # def test_schedule_page(self):
    #     self.client.login()
    #     response = self.client.get(reverse('aquaholic:schedule'))
    #     self.assertEqual(response.status_code, 200)

    def test_set_schedule(self):
        self.client.login()
        first_notify_time = datetime.time(10, 0, 0)
        last_notify_time = datetime.time(22, 0, 0)
        user = create_userinfo(80, 0, first_notify_time, last_notify_time)
        user.total_hours = get_total_hours(first_notify_time, last_notify_time)
        self.assertEqual(user.total_hours, 12)
        # self.assertEqual()
        first_notify_time = datetime.time(11, 0, 0)
        user.objects.create(user_info_id=user,
                                    notification_time=first_notify_time,
                                    expected_amount=user.get_water_amount_per_hour(),
                                    notification_status=False)
