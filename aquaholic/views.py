"""Views for Aquaholic application."""
import datetime
import calendar
from decouple import config
from django.views import generic
from django.shortcuts import reverse, render
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Schedule, Intake, UserInfo, KILOGRAM_TO_POUND, OUNCES_TO_MILLILITER
from .notification import get_access_token, send_notification, check_token_status


def get_total_hours(first_notification_time, last_notification_time):
    """Calculate total hours from first and last notification time."""
    date = datetime.date(1, 1, 1)
    first_time = datetime.datetime.combine(date, first_notification_time)
    last_time = datetime.datetime.combine(date, last_notification_time)
    time = last_time - first_time
    return round(time.seconds / 3600)


def login_alert(request):
    """Alert from login using line."""
    return render(request, 'aquaholic/alert.html')


class HomePageView(generic.ListView):
    """A class that represents the home page view."""

    template_name = 'aquaholic/home.html'

    def get(self, request, *args, **kwargs):
        """User is authenticated redirect to different page to unauthenticated user."""
        user = request.user
        # intake date default time is 10 am
        date = make_aware(datetime.datetime.today().replace(hour=10, minute=0, second=0, microsecond=0))
        if not user.is_authenticated:
            return render(request, self.template_name)
        # for new user, create new user info
        if not UserInfo.objects.filter(user_id=user.id).exists():
            UserInfo.objects.create(user_id=user.id)
        user_info = UserInfo.objects.get(user_id=user.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(user.id,)))
        if not Intake.objects.filter(user_info_id=user_info.id, date=date).exists():
            return render(request, self.template_name,
                          {"user_intake_percentage": 0,
                           "goal": user_info.water_amount_per_day,
                           "user_intake": 0})
        user_intake = Intake.objects.get(user_info_id=user_info.id, date=date)
        goal = user_info.water_amount_per_day
        intake = user_intake.total_amount
        if goal != 0:
            user_intake_percentage = int(intake / goal * 100)
            if user_intake_percentage > 100:
                user_intake_percentage = 100
            return render(request, self.template_name, {"user_intake_percentage": user_intake_percentage,
                                                        "user_intake": int(intake),
                                                        "goal": user_info.water_amount_per_day})
        return render(request, self.template_name,
                      {"user_intake_percentage": 0,
                       "goal": user_info.water_amount_per_day,
                       "user_intake": int(intake)})


class AboutUsView(generic.ListView):
    """A class that represents the about us page view."""

    template_name = 'aquaholic/about_us.html'

    def get(self, request, *args, **kwargs):
        """Information about application and creator."""
        return render(request, self.template_name)


class CalculateView(generic.ListView):
    """A class that represents the calculation page view."""

    template_name = 'aquaholic/calculate.html'

    def get(self, request, *args, **kwargs):
        """Calculate page for unauthenticated user."""
        return render(request, self.template_name)

    def post(self, request):
        """Water amount per day calculate from user weight and exercise duration for unauthenticated user."""
        try:
            weight = float(request.POST["weight"])
            exercise_duration = float(request.POST["exercise_duration"])
        except ValueError:
            message = "Please, enter numbers in both fields."
            return render(request, self.template_name,
                          {'message': message})
        water_amount_per_day = int(((weight * KILOGRAM_TO_POUND * 0.5) + (exercise_duration / 30) * 12) * OUNCES_TO_MILLILITER)
        return render(request, self.template_name,
                      {'result': water_amount_per_day})


class ProfileView(LoginRequiredMixin, generic.DetailView):
    """A class that represents the user's profile page view."""

    template_name = "aquaholic/profile.html"

    def get(self, request, *args, **kwargs):
        """Get all the information of authenticated user."""
        user = request.user
        user_info = UserInfo.objects.get(user_id=user.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(user.id,)))
        date_join = user.date_joined.date()
        return render(request, self.template_name, {"first_name": f'{user.first_name}',
                                                    "weight": f"{user_info.weight}",
                                                    "exercise_duration": f"{user_info.exercise_duration}",
                                                    "join": f"{date_join}",
                                                    "user_id": f"{user.id}"})


class RegistrationView(LoginRequiredMixin, generic.DetailView):
    """A class that represents the calculation page view for new authenticated user."""

    template_name = 'aquaholic/regis.html'

    def get(self, request, *args, **kwargs):
        """Calculate page for authenticated user."""
        user_info = UserInfo.objects.get(user_id=request.user.id)
        if user_info.weight == 0:
            return render(request, self.template_name)
        return render(request, self.template_name,
                      {'result': user_info.water_amount_per_day,
                       'weight': user_info.weight,
                       'exercise_duration': user_info.exercise_duration})

    def post(self, request, *args, **kwargs):
        """Water amount per day calculate from user weight and exercise duration for authenticated user."""
        try:
            user_info = UserInfo.objects.get(user_id=request.user.id)
            user_info.weight = float(request.POST["weight"])
            user_info.exercise_duration = float(request.POST["exercise_duration"])
        except ValueError:
            message = "Please, enter numbers in both fields."
            return render(request, self.template_name,
                          {'message': message})
        user_info.set_water_amount_per_day()
        user_info.set_water_amount_per_hour()
        user_info.save()
        if user_info.water_amount_per_day == 0:
            return render(request, 'aquaholic/regis.html',
                          {'result': user_info.water_amount_per_day,
                           'weight': user_info.weight,
                           'exercise_duration': user_info.exercise_duration})
        # update schedule
        all_schedules = Schedule.objects.filter(user_info_id=user_info.id)
        for one_schedule in all_schedules:
            one_schedule.expected_amount = user_info.water_amount_per_hour
            one_schedule.save()
        return render(request, self.template_name,
                      {'result': user_info.water_amount_per_day,
                       'weight': user_info.weight,
                       'exercise_duration': user_info.exercise_duration})


class CalculateAuthView(LoginRequiredMixin, generic.DetailView):
    """A class that represents the calculation page view for authenticate user."""

    template_name = 'aquaholic/calculation_auth.html'

    def get(self, request, *args, **kwargs):
        """Calculate page for authenticated user."""
        user_info = UserInfo.objects.get(user_id=request.user.id)
        if user_info.weight == 0:
            return render(request, self.template_name)
        return render(request, self.template_name,
                      {'result': user_info.water_amount_per_day,
                       'weight': user_info.weight,
                       'exercise_duration': user_info.exercise_duration})

    def post(self, request, *args, **kwargs):
        """Water amount per day calculate from user weight and exercise duration for authenticated user."""
        try:
            user_info = UserInfo.objects.get(user_id=request.user.id)
            user_info.weight = float(request.POST["weight"])
            user_info.exercise_duration = float(request.POST["exercise_duration"])
        except ValueError:
            message = "Please, enter numbers in both fields."
            return render(request, self.template_name,
                          {'message': message})
        user_info.set_water_amount_per_day()
        user_info.set_water_amount_per_hour()
        user_info.save()
        # update schedule
        all_schedules = Schedule.objects.filter(user_info_id=user_info.id)
        for one_schedule in all_schedules:
            one_schedule.expected_amount = user_info.water_amount_per_hour
            one_schedule.save()
        return render(request, self.template_name,
                      {'result': user_info.water_amount_per_day,
                       'weight': user_info.weight,
                       'exercise_duration': user_info.exercise_duration})


class SetUpRegistrationView(LoginRequiredMixin, generic.DetailView):
    """A class that represents the set up page view."""

    template_name = 'aquaholic/set_up_regist.html'

    def get(self, request, *args, **kwargs):
        """Go to set up registration page for new user."""
        user_info = UserInfo.objects.get(user_id=request.user.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        status = check_token_status(user_info.notify_token)
        return render(request, self.template_name,
                      {"has_token": status == 200})


class SetUpView(LoginRequiredMixin, generic.DetailView):
    """A class that represents the set up page view."""

    template_name = 'aquaholic/set_up.html'

    def get(self, request, *args, **kwargs):
        """Set up schedule page."""
        user_info = UserInfo.objects.get(user_id=request.user.id)
        first = user_info.first_notification_time.strftime("%H:%M")
        last = user_info.last_notification_time.strftime("%H:%M")
        noti_hour = int(user_info.time_interval)
        status = check_token_status(user_info.notify_token)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        return render(request, self.template_name, {'first_notification': first,
                                                    'last_notification': last,
                                                    'notification_hour': noti_hour,
                                                    "has_token": status == 200})

    def post(self, request, *args, **kwargs):
        """Handle tasks after user clicked save.

        Update the database and redirect user to line
        notify authorization or schedule page in case that
        the user already has notify token. User will stay on
        set up page if the value is invalid.
        """
        user_info = UserInfo.objects.get(user_id=request.user.id)
        try:
            first = request.POST["first_notification"]
            last = request.POST["last_notification"]
            interval = int(request.POST["notify_interval"])
            first_notify_time = datetime.datetime.strptime(first, "%H:%M").time()
            last_notify_time = datetime.datetime.strptime(last, "%H:%M").time()
        except ValueError:
            message = "Please, enter time in both fields."
            user_info = UserInfo.objects.get(user_id=request.user.id)
            status = check_token_status(user_info.notify_token)
            return render(request, self.template_name,
                          {'message': message,
                           "first_notification": user_info.first_notification_time.strftime("%H:%M"),
                           "last_notification": user_info.last_notification_time.strftime("%H:%M"),
                           "notification_hour": user_info.time_interval,
                           "has_token": status == 200})
        if first == last or get_total_hours(first_notify_time, last_notify_time) == 0:
            message = "Please, enter different time or time difference is more than 1 hour."
            return render(request, self.template_name,
                          {'message': message})
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        self.update_user_info(first_notify_time, last_notify_time, interval, user_info)
        self.delete_schedule(user_info)  # remove all old schedules if any
        self.create_schedule(user_info)  # create new schedule
        status = check_token_status(user_info.notify_token)
        message = "Saved! Please, visit schedule page to see the update."
        return render(request, self.template_name,
                      {'message': message,
                       'first_notification': user_info.first_notification_time.strftime("%H:%M"),
                       'last_notification': user_info.last_notification_time.strftime("%H:%M"),
                       'notification_hour': interval,
                       "has_token": status == 200})

    @staticmethod
    def update_user_info(first_notify_time, last_notify_time, interval, user_info):
        """Save new user information to the database."""
        user_info.first_notification_time = first_notify_time
        user_info.last_notification_time = last_notify_time
        user_info.time_interval = interval
        # calculate and save total hours and water amount per hour to database
        user_info.total_hours = get_total_hours(user_info.first_notification_time,
                                                user_info.last_notification_time)
        user_info.set_water_amount_per_hour()
        user_info.save()

    @staticmethod
    def create_schedule(user_info):
        """Create new schedule provided the new information given."""
        # get total hours, first notification time and expected amount (water amount to drink per hour)
        total_hours = int(user_info.total_hours)
        expected_amount = user_info.water_amount_per_hour
        interval = user_info.time_interval
        last_hour = total_hours - total_hours % interval
        first_notification_time = datetime.datetime.combine(datetime.date.today(),
                                                            user_info.first_notification_time)
        last_notification_time = first_notification_time + datetime.timedelta(hours=last_hour)
        # last notification time less than now, the schedule will notify tomorrow
        if last_notification_time < datetime.datetime.now():
            first_notification_time += datetime.timedelta(hours=24)
        notification_time = first_notification_time
        if user_info.notification_turned_on:
            for i in range(0, total_hours + 1, interval):
                Schedule.objects.create(user_info_id=user_info.id,
                                        notification_time=make_aware(notification_time),
                                        expected_amount=expected_amount,
                                        notification_status=(notification_time < datetime.datetime.now()),
                                        is_last=(i == last_hour)
                                        )
                notification_time += datetime.timedelta(hours=interval)
        else:
            for i in range(0, total_hours + 1, interval):
                Schedule.objects.create(user_info_id=user_info.id,
                                        notification_time=make_aware(notification_time),
                                        expected_amount=expected_amount,
                                        notification_status=True,
                                        is_last=(i == last_hour)
                                        )
                notification_time += datetime.timedelta(hours=interval)

    @staticmethod
    def delete_schedule(user_info):
        """Delete all the existing schedule for this user."""
        if Schedule.objects.filter(user_info_id=user_info.id).exists():
            found_schedule = Schedule.objects.filter(user_info_id=user_info.id)
            for one_schedule in found_schedule:
                one_schedule.delete()


class LineNotifyVerificationView(LoginRequiredMixin, generic.DetailView):
    """A class for handling line notify verification."""

    def get(self, request, *args, **kwargs):
        """Redirect to Line notify authorization."""
        url = f"https://notify-bot.line.me/oauth/authorize?response_type=code&client_id={config('CLIENT_ID_NOTIFY')}" \
              f"&redirect_uri={config('REDIRECT_URI_NOTIFY')}&scope=notify&state=testing123 "
        return HttpResponseRedirect(url)


class LineNotifyConnect(LoginRequiredMixin, generic.DetailView):
    """A class that represents line connect view that helps user connect to line notify."""

    def get(self, request, *args, **kwargs):
        """Go to line connect page."""
        user_info = UserInfo.objects.get(user_id=request.user.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        status = check_token_status(user_info.notify_token)
        return render(request, "aquaholic/line_connect.html",
                      {"has_token": status == 200})


class NotificationCallbackView(LoginRequiredMixin, generic.DetailView):
    """A class that handles the callback after user authorize notification."""

    def get(self, request, *args, **kwargs):
        """Send welcome message to new user and save generated token to user info."""
        code = request.GET['code']
        token = get_access_token(code)
        send_notification("Welcome to aquaholic", token)
        user_info = UserInfo.objects.get(user_id=request.user.id)
        user_info.notify_token = token
        user_info.save()
        return HttpResponseRedirect(reverse('aquaholic:line_connect', args=(request.user.id,)))


class ScheduleView(LoginRequiredMixin, generic.DetailView):
    """A class that represents the schedule page view."""

    model = Schedule
    template_name = 'aquaholic/schedule.html'

    def get(self, request, *args, **kwargs):
        """Illustrated the schedule for user."""
        user_info = UserInfo.objects.get(user_id=request.user.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        status = check_token_status(user_info.notify_token)
        return render(request, self.template_name,
                      {'schedule': Schedule.objects.filter(user_info_id=user_info.id),
                       'has_token': status == 200})

    def post(self, request, *args, **kwargs):
        """Notification of schedule."""
        status = request.POST['status']
        user_info = UserInfo.objects.get(user_id=request.user.id)
        user_schedule = Schedule.objects.filter(user_info_id=user_info.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        if status == "turn_off":
            user_info.notification_turned_on = False
            user_info.save()
            for row in user_schedule:
                row.notification_status = True
                row.save()
        else:
            user_info.notification_turned_on = True
            user_info.save()
            for row in user_schedule:
                row.notification_status = row.notification_time < timezone.now()
                row.save()
        status = check_token_status(user_info.notify_token)
        return render(request, self.template_name,
                      {'schedule': Schedule.objects.filter(user_info_id=user_info.id),
                       'has_token': status == 200})


class InputView(LoginRequiredMixin, generic.DetailView):
    """A class that represents the input page view."""

    model = Intake
    template_name = 'aquaholic/input.html'

    def get(self, request, *args, **kwargs):
        """Input schedule page."""
        user_info = UserInfo.objects.get(user_id=request.user.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Input the amount of water from user and save to database."""
        try:
            amount = float(request.POST["amount"])
            if amount <= 0:
                amount = 0
            date = request.POST["date"]
            intake_date = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(hours=10)
        except ValueError:
            message = "Please, input numbers in both fields."
            return render(request, self.template_name,
                          {'message': message})
        # default time for intake date is 10 am
        aware_date = make_aware(intake_date)
        user_info = UserInfo.objects.get(user_id=request.user.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        # User already have intake for the given day, add amount of water to existed amount
        if Intake.objects.filter(user_info_id=user_info.id, date=aware_date).exists():
            intake = Intake.objects.get(user_info_id=user_info.id, date=aware_date)
            intake.total_amount += amount
            intake.save()
        else:
            Intake.objects.create(user_info_id=user_info.id,
                                  date=aware_date,
                                  total_amount=amount)
        if amount <= 0:
            message = "Sorry! Water amount must be a positive number more than 0."
        else:
            message = "Saved !"
        return render(request, self.template_name,
                      {'message': message})


class HistoryView(LoginRequiredMixin, generic.DetailView):
    """A class that represents the history page view."""

    model = Intake
    template_name = 'aquaholic/history.html'

    def show_history(self, request, selected_year, selected_month):
        """Get the data needed for history page and send those data as a context to history.html."""
        num_days_in_month = calendar.monthrange(selected_year, selected_month)[1]
        reached_goal_amount = dict()
        not_reached_goal_amount = dict()
        for day in range(1, num_days_in_month + 1):
            reached_goal_amount[datetime.date(selected_year, selected_month, day).strftime("%d %b %Y")] = 0
            not_reached_goal_amount[datetime.date(selected_year, selected_month, day).strftime("%d %b %Y")] = 0
        user_info = UserInfo.objects.get(user_id=request.user.id)
        if user_info.water_amount_per_day == 0:
            return HttpResponseRedirect(reverse("aquaholic:registration", args=(request.user.id,)))
        goal = user_info.water_amount_per_day
        reached_goal = Intake.objects.filter(user_info_id=user_info.id,
                                             date__month=selected_month,
                                             date__year=selected_year,
                                             total_amount__gte=goal).order_by('date')
        not_reached_goal = Intake.objects.filter(user_info_id=user_info.id,
                                                 date__month=selected_month,
                                                 date__year=selected_year,
                                                 total_amount__lt=goal).order_by('date')
        for intake in reached_goal:
            reached_goal_amount[intake.date.strftime("%d %b %Y")] = intake.total_amount

        for intake in not_reached_goal:
            not_reached_goal_amount[intake.date.strftime("%d %b %Y")] = intake.total_amount

        return render(request, self.template_name, {"goal": goal,
                                                    "date": list(reached_goal_amount.keys()),
                                                    "reached_goal_data":
                                                        list(reached_goal_amount.values()),
                                                    "not_reached_goal_data":
                                                        list(not_reached_goal_amount.values()),
                                                    "recent_year": [datetime.datetime.now().year - i for i in range(5)],
                                                    "selected_month_int": selected_month,
                                                    "selected_month_str": datetime.date(2022, selected_month,
                                                                                        1).strftime('%b'),
                                                    "selected_year": selected_year,
                                                    })

    def get(self, request, *args, **kwargs):
        """Go to the history page showing the intake history of this month and year."""
        today = datetime.datetime.now()
        this_month = today.month
        this_year = today.year
        return self.show_history(request, this_year, this_month)

    def post(self, request, *args, **kwargs):
        """Go to the history page showing the intake history of selected month and year."""
        selected_month = int(request.POST['month'])
        selected_year = int(request.POST['year'])
        return self.show_history(request, selected_year, selected_month)


def update_notification(request):
    """Cron job for sending notification via line.

    Send notification to the user and update their status.
    Cron-job.org will call this view every 5 minutes to check
    if it's the time to send notification. After the last notification
    in a user's schedule is sent, the time in the schedule will be
    added by 24 hours.
    """
    all_to_send = Schedule.objects.filter(notification_time__lte=timezone.now(),
                                          notification_status=False)
    for one_to_send in all_to_send:
        send_notification(f"Don't forget to drink {one_to_send.expected_amount} ml of water",
                          one_to_send.user_info.notify_token)
        one_to_send.notification_status = True
        one_to_send.save()

    last_to_send = Schedule.objects.filter(notification_status=True, is_last=True,
                                           notification_time__lte=timezone.now())
    for last_schedule in last_to_send:
        user_info = last_schedule.user_info
        user_schedule = Schedule.objects.filter(user_info=user_info)
        if user_info.notification_turned_on:
            for schedule in user_schedule:
                schedule.notification_time += timezone.timedelta(hours=24)
                schedule.notification_status = False
                schedule.save()
        else:
            for schedule in user_schedule:
                schedule.notification_time += timezone.timedelta(hours=24)
                schedule.save()
    return HttpResponse()
