"""Unittests for aquaholic app."""
import datetime
from http import HTTPStatus
from unittest.mock import patch
from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from aquaholic.views import get_total_hours
from aquaholic.models import UserInfo, Intake, Schedule
from aquaholic.notification import get_access_token, send_notification, check_token_status


def create_userinfo(weight, exercise_time, first_notification_time, last_notification_time):
    """Create user info object with the providing information."""
    return UserInfo.objects.create(weight=weight,
                                   exercise_duration=exercise_time,
                                   first_notification_time=first_notification_time,
                                   last_notification_time=last_notification_time)


class UserInfoModelTests(TestCase):
    """Test user info model."""

    def test_amount_of_water(self):
        """Calculate the amount of water from user input weight and exercise time."""
        user = UserInfo(weight=50, exercise_duration=60)
        user.set_water_amount_per_day()
        amount = 2339.7265
        self.assertAlmostEqual(int(amount), user.water_amount_per_day, places=4)

    def test_get_total_hour(self):
        """Calculate the total hour from user input notification time."""
        user = create_userinfo(50, 60, first_notification_time=datetime.time(8, 0, 0),
                               last_notification_time=datetime.time(22, 0, 0))
        user.total_hours = get_total_hours(user.first_notification_time, user.last_notification_time)
        total = 14
        self.assertEqual(total, user.total_hours)

    def test_amount_per_hour(self):
        """Calculate the amount of water user to intake per hour."""
        user = create_userinfo(50, 60, first_notification_time=datetime.time(8, 0, 0),
                               last_notification_time=datetime.time(22, 0, 0))
        per_hour = 155.982
        user.set_water_amount_per_day()
        user.total_hours = get_total_hours(user.first_notification_time, user.last_notification_time)
        user.set_water_amount_per_hour()
        self.assertAlmostEqual(int(per_hour), user.water_amount_per_hour, 2)


class HomePageViewTests(TestCase):
    """Tests homepage view."""

    def test_home_page(self):
        """Redirect to homepage view to calculate water intake."""
        response = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_home_page(self):
        """Client redirect to home page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        cal_url = reverse('aquaholic:home')
        self.assertEqual(response.url, cal_url)

    def test_visit_home_page_with_zero_intake(self):
        """Visitor can visit home page with zero intake."""
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(user.id,)),
                         data={"weight": 50, "exercise_duration": 0})
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 200)

    def test_visit_home_page_with_intakes(self):
        """Visitor can visit home page with intakes."""
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(user.id,)),
                         data={"weight": 50, "exercise_duration": 0})
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 200)
        input_url = reverse('aquaholic:input', args=(user.id,))
        form_data = {"amount": 2000,
                     "date": "2022-11-25"}
        self.client.post(input_url, form_data)
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 200)


class CalculateViewTests(TestCase):
    """Test the calculate page for unauthenticated user."""

    def test_calculate_page(self):
        """Redirect to calculate page to calculate water intake."""
        response = self.client.get(reverse('aquaholic:calculate'))
        self.assertEqual(response.status_code, 200)

    def test_invalid_input(self):
        """Input invalid value."""
        response = self.client.post('/aquaholic/calculate', data={"weight": "weight", "exercise_duration": 0})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Please, enter numbers in both fields.", html=True)

    def test_calculation(self):
        """Calculate water amount correctly."""
        response = self.client.post('/aquaholic/calculate', data={"weight": 65, "exercise_duration": 120})
        self.assertContains(response, 3538)


class TemplateUsedTests(TestCase):
    """Test the template used in each page is correct."""

    def test_template_used(self):
        """Template used correctly."""
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
        self.client.login(username='testuser', password='12345')
        self.client.get(reverse('aquaholic:home'))
        # redirect to registration page as new user
        self.client.post(reverse("aquaholic:registration", args=(user.id,)), data={"weight": 50, "exercise_duration": 0})
        page = self.client.get(reverse('aquaholic:set_up', args=(user.id,)))
        self.assertTemplateUsed(page, 'aquaholic/set_up.html')
        self.client.post(reverse("aquaholic:set_up", args=(user.id,)), data={"first_notification": "11:00",
                                                                             "last_notification": "12:00",
                                                                             "notify_interval": 1})
        page = self.client.get(reverse('aquaholic:schedule', args=(user.id,)))
        self.assertTemplateUsed(page, 'aquaholic/schedule.html')
        page = self.client.get(reverse('aquaholic:alert'))
        self.assertTemplateUsed(page, 'aquaholic/alert.html')


class LoginWithLineTests(TestCase):
    """Tests for line login."""

    def test_authenticated_using_line(self):
        """After login redirect to calculation page."""
        self.client.login()
        cal_url = reverse('aquaholic:home')
        response = self.client.get(cal_url)
        self.assertEqual(response.status_code, 200)


class CalculateAuthViewTests(TestCase):
    """Test cases for calculate auth view."""

    def setUp(self) -> None:
        """Login and go register first."""
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        page1 = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page1.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(self.user.id,)),
                         data={"weight": 50, "exercise_duration": 0})

    def test_get_calculate_auth(self):
        """Go to calculate page for authenticated user."""
        response = self.client.get(reverse("aquaholic:calculate_auth", args=(self.user.id,)))
        self.assertEqual(response.status_code, 200)

    def test_calculation(self):
        """Calculation is done correctly."""
        response = self.client.post(reverse("aquaholic:calculate_auth", args=(self.user.id,)),
                                    data={"weight": 65, "exercise_duration": 120})
        self.assertContains(response, 3538)

    def test_invalid_input(self):
        """Input invalid value."""
        response = self.client.post(reverse("aquaholic:calculate_auth", args=(self.user.id,)),
                                    data={"weight": "weight", "exercise_duration": 0})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Please, enter numbers in both fields.", html=True)


class RegistrationViewTests(TestCase):
    """Test cases for registration view."""

    def setUp(self) -> None:
        """Login and go register first."""
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        page1 = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page1.status_code, 302)  # redirect to registration page

    def test_go_to_registration_page(self):
        """Go to registration page."""
        user = User.objects.create(username='testuser1')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser1', password='12345')
        page1 = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page1.status_code, 302)
        page2 = self.client.get(reverse('aquaholic:registration', args=(user.id,)))
        self.assertTemplateUsed(page2, "aquaholic/regis.html")

    def test_calculation(self):
        """Calculation is done correctly."""
        response = self.client.post(reverse("aquaholic:registration", args=(self.user.id,)),
                                    data={"weight": 65, "exercise_duration": 120})
        self.assertContains(response, 3538)

    def test_invalid_input(self):
        """Input invalid value."""
        response = self.client.post(reverse("aquaholic:registration", args=(self.user.id,)),
                                    data={"weight": "weight", "exercise_duration": 0})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Please, enter numbers in both fields.", html=True)
        response = self.client.post(reverse("aquaholic:registration", args=(self.user.id,)),
                                    data={"weight": 0, "exercise_duration": 0})
        self.assertEqual(response.status_code, HTTPStatus.OK)


class SetUpViewTests(TestCase):
    """Tests for set up view."""

    def setUp(self):
        """Login and register."""
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(self.user.id,)),
                         data={"weight": 50, "exercise_duration": 0})

    def test_go_to_set_up_page(self):
        """Can go to set notification page successfully."""
        page = self.client.get(reverse('aquaholic:set_up', args=(self.user.id,)))
        self.assertEqual(page.status_code, 200)

    def test_set_notification_time(self):
        """Can post data in set up view successfully."""
        response = self.client.post(reverse("aquaholic:set_up", args=(self.user.id,)),
                                    data={"first_notification": "11:00",
                                          "last_notification": "16:00",
                                          "notify_interval": 1})
        self.assertContains(response, "Saved! Please, visit schedule page to see the update.", html=True)

    def test_set_notification_time_is_not_allow(self):
        """Total hour in notification setting must greater than 0."""
        response = self.client.post(reverse("aquaholic:set_up", args=(self.user.id,)),
                                    data={"first_notification": "11:00",
                                          "last_notification": "11:00",
                                          "notify_interval": 1})
        self.assertContains(response, "Please, enter different time or time difference is more than 1 hour.", html=True)


class ScheduleViewTests(TestCase):
    """Test cases for schedule view."""

    def setUp(self):
        """Login, register, and go to schedule page."""
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(self.user.id,)),
                         data={"weight": 50, "exercise_duration": 0})
        page = self.client.get(reverse('aquaholic:schedule', args=(self.user.id,)))
        self.assertEqual(page.status_code, 200)

    def test_get_schedule(self):
        """Can go to schedule page successfully."""
        page = self.client.get(reverse('aquaholic:schedule', args=(self.user.id,)))
        self.assertEqual(page.status_code, 200)

    def test_turn_off_notification(self):
        """Set user_info.notification_turned_on == False when clicks turn off."""
        page = self.client.post(reverse('aquaholic:schedule', args=(self.user.id,)), data={'status': "turn_off"})
        self.assertEqual(page.status_code, 200)
        user_info1 = UserInfo.objects.get(user_id=self.user.id)
        self.assertFalse(user_info1.notification_turned_on)
        response = self.client.post(reverse("aquaholic:set_up", args=(self.user.id,)),
                                    data={"first_notification": "11:00",
                                          "last_notification": "16:00",
                                          "notify_interval": 1})
        self.assertContains(response, "Saved! Please, visit schedule page to see the update.", html=True)
        page = self.client.post(reverse('aquaholic:schedule', args=(self.user.id,)), data={'status': "turn_off"})
        self.assertEqual(page.status_code, 200)
        user_info1 = UserInfo.objects.get(user_id=self.user.id)
        self.assertFalse(user_info1.notification_turned_on)

    def test_turn_on_notification(self):
        """Set user_info.notification_turned_on == True when clicks turn on."""
        page = self.client.post(reverse('aquaholic:schedule', args=(self.user.id,)), data={'status': "turn_on"})
        self.assertEqual(page.status_code, 200)
        user_info1 = UserInfo.objects.get(user_id=self.user.id)
        self.assertTrue(user_info1.notification_turned_on)


class HistoryViewTests(TestCase):
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
        self.client.login(username='testuser', password='12345')
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(user.id,)), data={"weight": 50, "exercise_duration": 0})
        response = self.client.get(reverse('aquaholic:history', args=(user.id,)))
        self.assertEqual(response.status_code, 200)
        history_url = reverse('aquaholic:history', args=(user.id,))

        # user change mouth and year of history page
        form_data = {"month": "12",
                     "year": "2021"}
        response = self.client.post(history_url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aquaholic/history.html')


class InputViewTests(TestCase):
    """Test cases for input view."""

    def test_input_page(self):
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
        self.client.login(username='testuser1', password='12345')
        self.client.get(reverse('aquaholic:home'))
        response = self.client.get(reverse('aquaholic:input', args=(user1.id,)))
        self.assertEqual(response.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(user1.id,)), data={"weight": 50, "exercise_duration": 0})

        # user input the amount of water and save
        input_url = reverse('aquaholic:input', args=(user1.id,))
        response = self.client.get(input_url)
        self.assertEqual(response.status_code, 200)
        form_data = {"amount": "200",
                     "date": "2022-11-05"}
        response = self.client.post(input_url, form_data)
        self.assertEqual(response.status_code, 200)

        # get userInfo object from database
        user_info = UserInfo.objects.get(user_id=user1.id)

        # datetime in database = actual time + 10 hours
        db_time = timezone.make_aware(datetime.datetime(2022, 11, 5) + datetime.timedelta(hours=10))
        intake1 = Intake.objects.get(user_info_id=user_info.id, date=db_time)
        self.assertEqual(200, intake1.total_amount)

        # user save the amount of water and save again
        input_url = reverse('aquaholic:input', args=(user1.id,))
        form_data = {"amount": "500",
                     "date": "2022-11-05"}
        response = self.client.post(input_url, form_data)
        self.assertEqual(response.status_code, 200)

        # the amount of water topped up from the already existing amount
        db_time = timezone.make_aware(datetime.datetime(2022, 11, 5) + datetime.timedelta(hours=10))
        intake1 = Intake.objects.get(user_info_id=user_info.id, date=db_time)
        self.assertEqual(700, intake1.total_amount)

    def test_input_invalid(self):
        """User amount of water input must be greater than 0."""
        # user logins and to home page where user info is created
        user1 = User.objects.create(username='testuser1')
        user1.set_password('12345')
        user1.save()
        self.client.login(username='testuser1', password='12345')
        response = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(response.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(user1.id,)), data={"weight": 50, "exercise_duration": 0})
        # user input the amount of water and save
        input_url = reverse('aquaholic:input', args=(user1.id,))
        form_data = {"amount": "0",
                     "date": "2022-11-25"}
        response = self.client.post(input_url, form_data)
        self.assertContains(response, "Please, input a number more than 0.", html=True)

    def test_not_input_in_both_fields(self):
        """User save input without amount of water and date."""
        # user logins and to home page where user info is created
        user1 = User.objects.create(username='testuser1')
        user1.set_password('12345')
        user1.save()
        self.client.login(username='testuser1', password='12345')
        response = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(response.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(user1.id,)),
                         data={"weight": 50, "exercise_duration": 0})
        # user input the amount of water and save
        input_url = reverse('aquaholic:input', args=(user1.id,))
        form_data = {"amount": "0",
                     "date": "0"}
        response = self.client.post(input_url, form_data)
        self.assertContains(response, "Please, input numbers in both fields.", html=True)


class AlertViewTests(TestCase):
    """Test alert view."""

    def test_unauthenticated_user_cannot_go_to_login_required_page(self):
        """Unauthenticated user will be redirected to alert page if they are not logged in."""
        user1 = User.objects.create(username='testuser1')
        user1.set_password('12345')
        user1.save()
        response = self.client.get(reverse('aquaholic:profile', args=(user1.id,)))
        self.assertEqual(response.status_code, 302)


class NotificationTests(TestCase):
    """Tests for methods in notification.py."""

    def test_token_is_invalid(self):
        """Cannot send notification with invalid token.

        Send message with token == None return None.
        Send message with token == invalid token return 401.
        """
        self.assertIsNone(send_notification("Hi", None))
        self.assertEqual(401, send_notification("Hi", "kfdljsfkdlfj"))

    def test_check_invalid_token_status(self):
        """Check status will not return 100 for invalid token."""
        invalid_token = "askjhdjkas"
        none_token = None
        self.assertNotEqual(check_token_status(invalid_token), 200)
        self.assertNotEqual(check_token_status(none_token), 200)

    def test_get_access_token_with_invalid_code(self):
        """Return None when input invalid code."""
        self.assertEqual(get_access_token("asjadk"), None)


class UpdateNotificationViewTests(TestCase):
    """Tests for update notification view."""

    def test_get_update_notification_view(self):
        """Can go to update notification view successfully."""
        response = self.client.get(reverse('aquaholic:cron'))
        self.assertEqual(response.status_code, 200)

    def test_schedule_updates_correctly(self):
        """Schedule is updated correctly when visiting cron url.

        When the time passes the scheduled time, notification status is changed to True.
        When the last schedule is sent, all schedule will be added by 24 hours
        and notification status is changed to False again.
        """
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser', password='12345')
        page = self.client.get(reverse('aquaholic:home'))
        self.assertEqual(page.status_code, 302)  # redirect to registration page
        self.client.post(reverse("aquaholic:registration", args=(user.id,)),
                         data={"weight": 50, "exercise_duration": 0})
        response = self.client.post(reverse("aquaholic:set_up", args=(user.id,)),
                                    data={"first_notification": "19:00",
                                          "last_notification": "21:00",
                                          "notify_interval": 1})
        self.assertContains(response, "Saved! Please, visit schedule page to see the update.", html=True)
        user_info = UserInfo.objects.get(user_id=user.id)
        last_schedule = Schedule.objects.filter(user_info_id=user_info.id, is_last=True).first()
        first_schedule = Schedule.objects.filter(user_info_id=user_info.id).first()
        first_schedule_time = first_schedule.notification_time
        last_schedule_time = last_schedule.notification_time
        self.assertFalse(last_schedule.notification_status)
        with patch.object(timezone, 'now', return_value=first_schedule_time + timezone.timedelta(minutes=10)):
            response = self.client.get(reverse('aquaholic:cron'))
            self.assertEqual(response.status_code, 200)
            new_first_schedule = Schedule.objects.filter(user_info_id=user_info.id).first()
            self.assertTrue(new_first_schedule.notification_status)
        with patch.object(timezone, 'now', return_value=last_schedule_time + timezone.timedelta(minutes=10)):
            response = self.client.get(reverse('aquaholic:cron'))
            self.assertEqual(response.status_code, 200)
            new_last_schedule = Schedule.objects.filter(user_info_id=user_info.id,
                                                        is_last=True).first()
            new_last_schedule_time = new_last_schedule.notification_time
            tomorrow = (timezone.now() + timezone.timedelta(days=1)).strftime("%Y %B %d")
            self.assertEqual(tomorrow, new_last_schedule_time.strftime("%Y %B %d"))
            self.assertFalse(new_last_schedule.notification_status)


class LineNotifyConnectViewTests(TestCase):
    """Tests for line notify connect view."""

    def test_get_line_connect(self):
        """Can visit to line connect view."""
        user1 = User.objects.create(username='testuser1')
        user1.set_password('12345')
        user1.save()
        self.client.login(username='testuser1', password='12345')
        self.client.get(reverse("aquaholic:home"))
        self.client.post(reverse("aquaholic:registration", args=(user1.id,)),
                         data={"weight": 50, "exercise_duration": 0})
        response = self.client.get(reverse('aquaholic:line_connect', args=(user1.id,)))
        self.assertEqual(response.status_code, 200)


class ProfileViewTests(TestCase):
    """Test cases for profile view."""

    def test_profile_page(self):
        """Authenticated user can view their profile."""
        user = User.objects.create(username='testuser1')
        user.set_password('12345')
        user.save()
        self.client.login(username='testuser1', password='12345')
        self.client.get(reverse("aquaholic:home"))
        response = self.client.get(reverse('aquaholic:profile', args=(user.id,)))
        # redirect to registration page
        self.assertEqual(response.status_code, 302)
        self.client.post(reverse("aquaholic:registration", args=(user.id,)), data={"weight": 60, "exercise_duration": 70})
        response = self.client.get(reverse('aquaholic:profile', args=(user.id,)))
        self.assertEqual(response.status_code, 200)


class AboutUsViewTests(TestCase):
    """Test about us view."""

    def test_go_to_about_us_page(self):
        """Any users can visit about us page."""
        response = self.client.get(reverse("aquaholic:about_us"))
        self.assertEqual(response.status_code, 200)
