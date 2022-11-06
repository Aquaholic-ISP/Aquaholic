import datetime
from aquaholic.models import UserInfo, Intake
from django.urls import reverse
from http import HTTPStatus
from django.test import TestCase, Client
from aquaholic.views import *
from django.contrib.auth.models import User


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
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        client = Client()
        client.login(username='testuser', password='12345')
        page = client.get(reverse('aquaholic:set_up', args=(user.id,)))
        self.assertTemplateUsed(page, 'aquaholic/set_up.html')

        userinfo = UserInfo.objects.create(weight=50, exercise_time=30, first_notification_time=datetime.time(8,0,0),
                                           last_notification_time=datetime.time(22 , 0,0), user_id=user.id)
        first_notify_time = userinfo.first_notification_time
        first_notification_time = datetime.datetime.combine(datetime.date.today(), first_notify_time)
        userinfo.total_hours = get_total_hours(userinfo.first_notification_time,
                                               userinfo.last_notification_time)
        userinfo.get_water_amount_per_hour()
        userinfo.save()
        expected_amount = userinfo.water_amount_per_hour
        Schedule.objects.create(user_info_id=user.id,
                                notification_time=first_notification_time,
                                expected_amount=expected_amount,
                                notification_status=False
                                )
        userinfo.save()
        page = client.get(reverse('aquaholic:schedule', args=(user.id,)))
        self.assertTemplateUsed(page, 'aquaholic/schedule.html')


class LoginWithLine(TestCase):
    def test_authenticated_using_line(self):
        """After login redirect to calculation page"""
        self.client.login()
        cal_url = reverse('aquaholic:home')
        response = self.client.get(cal_url)
        self.assertEqual(response.status_code, 200)


class SetUpView(TestCase):
    def test_setup_page(self):
        """ authenticated user can redirect to set up page"""
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        client = Client()
        client.login(username='testuser', password='12345')
        page = client.get(reverse('aquaholic:set_up', args=(user.id,)))
        self.assertEqual(page.status_code, 200)

    def test_get_notification_time(self):
        """User can set notification time in set up page."""
        first_notify_time = datetime.time.strftime(datetime.time(10, 0, 0), "%H:%M")
        last_notify_time = datetime.time.strftime(datetime.time(22, 0, 0), "%H:%M")
        self.client.login()
        user = create_userinfo(80, 0, first_notify_time, last_notify_time)
        self.assertEqual(user.first_notification_time, "10:00")
        self.assertEqual(user.last_notification_time, "22:00")


class ScheduleView(TestCase):
    def test_new_user_schedule_page_not_found(self):
        """Authenticated user can redirect to schedule page. But no time and amount in schedule page
        if users are not create schedule."""
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        client = Client()
        client.login(username='testuser', password='12345')
        userinfo = UserInfo.objects.create(weight=50, exercise_time=30, first_notification_time=datetime.time(11, 0, 0),
                                           last_notification_time=datetime.time(22, 0, 0), user_id=user.id)
        userinfo.total_hours = get_total_hours(userinfo.first_notification_time,
                                               userinfo.last_notification_time)
        userinfo.get_water_amount_per_hour()
        userinfo.save()
        page = client.get(reverse('aquaholic:schedule', args=(user.id,), ))
        self.assertEqual(page.status_code, 200)

    def test_set_schedule(self):
        """schedule show time nad amount after generate schedule."""
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        client = Client()
        client.login(username='testuser', password='12345')
        userinfo = UserInfo.objects.create(weight=50, exercise_time=30, first_notification_time=datetime.time(11, 0, 0),
                                           last_notification_time=datetime.time(22, 0, 0), user_id=user.id)
        userinfo.total_hours = get_total_hours(userinfo.first_notification_time,
                                               userinfo.last_notification_time)
        userinfo.get_water_amount_per_hour()
        userinfo.save()
        first_notify_time = userinfo.first_notification_time
        expected_amount = userinfo.water_amount_per_hour
        first_notification_time = datetime.datetime.combine(datetime.date.today(), first_notify_time)
        Schedule.objects.create(user_info_id=userinfo.id,
                                    notification_time=first_notification_time,
                                    expected_amount=expected_amount,
                                    notification_status=False
                                    )
        page = client.get(reverse('aquaholic:schedule', args=(user.id,),))
        self.assertEqual(page.status_code, 200)


class HistoryViewTest(TestCase):
    """Test cases for history page."""
    def test_history_page(self):
        """History view work correctly.

        When user go to history page,
        it showed water intake of user
        base on month and year that user selected.
        """
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        client = Client()
        client.login(username='testuser', password='12345')
        first_notify_time = datetime.time(8, 0, 0)
        last_notify_time = datetime.time(23, 0, 0)
        userinfo = UserInfo.objects.create(weight=50,
                                           exercise_time=60,
                                           first_notification_time=first_notify_time,
                                           last_notification_time=last_notify_time,
                                           user_id=user.id)
        response = client.get(reverse('aquaholic:home'))
        self.assertEqual(response.status_code, 200)

        # user input amount of water and go to history page
        Intake.objects.create(user_info_id=userinfo.id,
                              intake_date=datetime.datetime.today(),
                              user_drinks_amount=500)
        response = client.get(reverse('aquaholic:history', args=(user.id,)))
        self.assertEqual(response.status_code, 200)
        history_url = reverse('aquaholic:history', args=(user.id,))

        # user change mouth and year of history page
        form_data = {"month": "12",
                     "year": "2021"}
        response = client.post(history_url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aquaholic/history.html')


class InputViewTest(TestCase):
    """Test cases for input view."""

    def test_input(self):
        """Intakes are stored in the database correctly.

        When user input an amount of water and save,
        the amount of water that the user input on
        the selected day topped up from the already
        existing amount in the database of that day.
        """
        # user logins and to home page where user info is created
        user1 = User.objects.create(username='testuser1')
        user1.set_password('12345')
        user1.save()
        client = Client()
        client.login(username='testuser1', password='12345')
        response = client.get(reverse('aquaholic:home'))
        self.assertEqual(response.status_code, 200)

        # user input the amount of water and save
        input_url = reverse('aquaholic:input', args=(user1.id,))
        form_data = {"amount": "200",
                     "date": "2022-11-05"}
        response = client.post(input_url, form_data)
        self.assertEqual(response.status_code, 302)

        # get userInfo object from database
        user_info = UserInfo.objects.get(user_id=user1.id)

        # datetime in database = actual time + 10 hours
        db_time = datetime.datetime(2022, 11, 5) + datetime.timedelta(hours=10)
        intake1 = Intake.objects.get(user_info_id=user_info.id, intake_date=db_time)
        self.assertEqual(200, intake1.user_drinks_amount)

        # user save the amount of water and save again
        input_url = reverse('aquaholic:input', args=(user1.id,))
        form_data = {"amount": "500",
                     "date": "2022-11-05"}
        response = client.post(input_url, form_data)
        self.assertEqual(response.status_code, 302)

        # the amount of water topped up from the already existing amount
        db_time = datetime.datetime(2022, 11, 5) + datetime.timedelta(hours=10)
        intake1 = Intake.objects.get(user_info_id=user_info.id, intake_date=db_time)
        self.assertEqual(700, intake1.user_drinks_amount)
