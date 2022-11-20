"""Views for Aquaholic application."""
import datetime
import calendar
from decouple import config
from django.views import generic
from django.shortcuts import reverse, render
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.timezone import make_aware
from .models import Schedule, Intake, UserInfo, KILOGRAM_TO_POUND, OUNCES_TO_MILLILITER
from .notification import get_access_token, send_notification


def get_total_hours(first_notification_time, last_notification_time):
    """Calculate total hours from first and last notification time."""
    date = datetime.date(1, 1, 1)
    first_time = datetime.datetime.combine(date, first_notification_time)
    last_time = datetime.datetime.combine(date, last_notification_time)
    time = last_time - first_time
    return round(time.seconds / 3600)


class HomePageView(generic.ListView):
    """A class that represents the home page view."""

    template_name = 'aquaholic/home.html'

    def get(self, request, *args, **kwargs):
        """User is authenticated redirect to different page to unauthenticated user."""
        user = request.user
        # intake date default time is 10 am
        date = datetime.datetime.today().replace(hour=10, minute=0, second=0, microsecond=0)
        if user.is_authenticated:
            # for new user, create new user info
            if not UserInfo.objects.filter(user_id=user.id).exists():
                UserInfo.objects.create(user_id=user.id)
            user_info = UserInfo.objects.get(user_id=user.id)
            if user_info.water_amount_per_day == 0:
                return render(request, 'aquaholic/register.html')
            if Intake.objects.filter(user_info_id=user_info.id, date=date).exists():
                all_intake = Intake.objects.get(user_info_id=user_info.id, date=date)
                if all_intake:
                    goal = user_info.water_amount_per_day
                    intake = all_intake.total_amount
                    all_intake_percentage = int(intake / goal * 100)
                    if all_intake_percentage <= 100:
                        return render(request, self.template_name, {"all_intake_percentage": f"{all_intake_percentage}",
                                                                    "all_intake": f"{intake}",
                                                                    "goal": f"{user_info.water_amount_per_day:.2f}"})
                    elif all_intake_percentage > 100:
                        all_intake_percentage = 100
                        return render(request, self.template_name, {" all_intake_percentage": f"{all_intake_percentage}",
                                                                    "all_intake": f"{intake}",
                                                                    "goal": f"{user_info.water_amount_per_day:.2f}"})
            return render(request, self.template_name, {"goal": f"{user_info.water_amount_per_day:.2f}"})
        return render(request, self.template_name)


class AboutUsView(generic.ListView):
    """A class that represents the about us page view."""

    template_name = 'aquaholic/about_us.html'

    def get(self, request, *args, **kwargs):
        """Information about application and creator."""
        return render(request, self.template_name)


class ProfileView(generic.DetailView):
    """A class that represents the user's profile page view."""

    template_name = "aquaholic/profile.html"

    def get(self, request, *args, **kwargs):
        """Get all the information of authenticated user."""
        user = request.user
        user_info = UserInfo.objects.get(user_id=user.id)
        date_join = user.date_joined.date()
        return render(request, self.template_name, {"first_name": f'{user.first_name}',
                                                    "weight": f"{user_info.weight}",
                                                    "exercise_duration": f"{user_info.exercise_duration}",
                                                    "join": f"{date_join}",
                                                    "user_id": f"{user.id}"})


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
            water_amount_per_day = ((weight * KILOGRAM_TO_POUND * 0.5) + (exercise_duration / 30) * 12) \
                                   * OUNCES_TO_MILLILITER
            return render(request, self.template_name,
                          {'result': f"{water_amount_per_day:.2f}"})
        except ValueError:
            message = "Please, enter numbers in both fields."
            return render(request, self.template_name,
                          {'message': message})


class RegistrationView(generic.DetailView):
    """A class that represents the calculation page view for new authenticated user."""

    template_name = 'aquaholic/register.html'

    def get(self, request, *args, **kwargs):
        """Registration page for new authenticated user."""
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Water amount per day calculate from user weight and exercise duration for new authenticated user."""
        try:
            user_info = UserInfo.objects.get(user_id=request.user.id)
            user_info.weight = float(request.POST["weight"])
            user_info.exercise_duration = float(request.POST["exercise_duration"])
            user_info.set_water_amount_per_day()
            user_info.set_water_amount_per_hour()
            user_info.save()

            if user_info.water_amount_per_day == 0:
                return render(request, 'aquaholic/register.html',
                              {'result': f"{round(user_info.water_amount_per_day):.2f}"})

            # update schedule
            all_schedules = Schedule.objects.filter(user_info_id=user_info.id)
            for one_schedule in all_schedules:
                one_schedule.expected_amount = round(user_info.water_amount_per_hour, 2)
                one_schedule.save()
            return render(request, self.template_name,
                          {'result': f"{user_info.water_amount_per_day:.2f}"})
        except ValueError:
            message = "Please, enter numbers in both fields."
            return render(request, self.template_name,
                          {'message': message})


class CalculateAuthView(generic.DetailView):
    """A class that represents the calculation page view for authenticate user."""

    template_name = 'aquaholic/calculation_auth.html'

    def get(self, request, *args, **kwargs):
        """Calculate page for authenticated user."""
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Water amount per day calculate from user weight and exercise duration for authenticated user."""
        try:
            user_info = UserInfo.objects.get(user_id=request.user.id)
            user_info.weight = float(request.POST["weight"])
            user_info.exercise_duration = float(request.POST["exercise_duration"])
            user_info.set_water_amount_per_day()
            user_info.set_water_amount_per_hour()
            user_info.save()

            if user_info.water_amount_per_day == 0:
                return render(request, 'aquaholic/register.html',
                              {'result': f"{round(user_info.water_amount_per_day):.2f}"})

            # update schedule
            all_schedules = Schedule.objects.filter(user_info_id=user_info.id)
            for one_schedule in all_schedules:
                one_schedule.expected_amount = round(user_info.water_amount_per_hour, 2)
                one_schedule.save()
            return render(request, self.template_name,
                          {'result': f"{user_info.water_amount_per_day:.2f}"})
        except ValueError:
            message = "Please, enter numbers in both fields."
            return render(request, self.template_name,
                          {'message': message})


class SetUpView(generic.DetailView):
    """A class that represents the set up page view."""

    template_name = 'aquaholic/set_up.html'

    def get(self, request, *args, **kwargs):
        """Set up schedule page."""
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Handle tasks after user clicked save.

        Update the database and redirect user to line
        notify authorization or schedule page in case that
        the user already has notify token. User will stay on
        set up page if the value is invalid.
        """
        try:
            first = request.POST["first_notification"]
            last = request.POST["last_notification"]
            step = int(request.POST["notify_step"])
            first_notify_time = datetime.datetime.strptime(first, "%H:%M").time()
            last_notify_time = datetime.datetime.strptime(last, "%H:%M").time()
            if first == last or get_total_hours(first_notify_time, last_notify_time) == 0:
                message = "Please, enter different time or time difference is more than 1 hour."
                return render(request, self.template_name,
                              {'message': message})
            user_info = UserInfo.objects.get(user_id=request.user.id)
            self.update_user_info(first_notify_time, last_notify_time, step, user_info)
            self.delete_schedule(user_info)  # remove all old schedules if any
            self.create_schedule(user_info, step)  # create new schedule

            if UserInfo.objects.get(user_id=request.user.id).notify_token is not None:
                return HttpResponseRedirect(reverse('aquaholic:schedule', args=(request.user.id,)))
            else:
                # redirect to line notify website for generate token
                url = f"https://notify-bot.line.me/oauth/authorize?response_type=code&client_id={config('CLIENT_ID_NOTIFY')}" \
                      f"&redirect_uri={config('REDIRECT_URI_NOTIFY')}&scope=notify&state=testing123 "
                return HttpResponseRedirect(url)
        except ValueError:
            message = "Please, enter time in both fields."
            return render(request, self.template_name,
                          {'message': message})

    @staticmethod
    def update_user_info(first_notify_time, last_notify_time, step, user_info):
        """Save new user information to the database."""
        user_info.first_notification_time = first_notify_time
        user_info.last_notification_time = last_notify_time
        user_info.time_interval = step
        # calculate and save total hours and water amount per hour to database
        user_info.total_hours = get_total_hours(user_info.first_notification_time,
                                                user_info.last_notification_time)
        user_info.set_water_amount_per_hour()
        user_info.save()

    @staticmethod
    def create_schedule(user_info, step):
        """Create new schedule provided the new information given."""
        # get total hours, first notification time and expected amount (water amount to drink per hour)
        total_hours = int(user_info.total_hours)
        expected_amount = user_info.water_amount_per_hour
        first_notification_time = datetime.datetime.combine(datetime.date.today(),
                                                            user_info.first_notification_time)
        last_notification_time = first_notification_time + datetime.timedelta(hours=total_hours)
        # last notification time less than now, the schedule will notify tomorrow
        if last_notification_time < datetime.datetime.now():
            first_notification_time += datetime.timedelta(hours=24)

        notification_time = first_notification_time
        for i in range(0, total_hours + 1, step):
            Schedule.objects.create(user_info_id=user_info.id,
                                    notification_time=notification_time,
                                    expected_amount=int(expected_amount),
                                    notification_status=(notification_time < datetime.datetime.now()),
                                    is_last=(i == total_hours)
                                    )
            notification_time += datetime.timedelta(hours=step)

    @staticmethod
    def delete_schedule(user_info):
        """Delete all the existing schedule for this user."""
        if Schedule.objects.filter(user_info_id=user_info.id).exists():
            found_schedule = Schedule.objects.filter(user_info_id=user_info.id)
            for one_schedule in found_schedule:
                one_schedule.delete()


class NotificationCallbackView(generic.DetailView):
    """A class that handles the callback after user authorize notification."""

    def get(self, request, *args, **kwargs):
        """Send welcome message to new user and save generated token to user info."""
        code = request.GET['code']
        token = get_access_token(code)
        send_notification("Welcome to aquaholic", token)
        user_info = UserInfo.objects.get(user_id=request.user.id)
        user_info.notify_token = token
        user_info.save()
        return HttpResponseRedirect(reverse('aquaholic:schedule', args=(request.user.id,)))


class ScheduleView(generic.DetailView):
    """A class that represents the schedule page view."""

    model = Schedule
    template_name = 'aquaholic/schedule.html'

    def get(self, request, *args, **kwargs):
        """Illustrated the schedule for user."""
        user_info = UserInfo.objects.get(user_id=request.user.id)
        return render(request, self.template_name,
                      {'schedule': Schedule.objects.filter(user_info_id=user_info.id)})

    def post(self, request, *args, **kwargs):
        """Notification of schedule."""
        status = request.POST['status']
        if status == "turn off":
            user_info = UserInfo.objects.get(user_id=request.user.id)
            user_schedule = Schedule.objects.filter(user_info_id=user_info.id)
            for row in user_schedule:
                row.notification_status = True
                row.save()
            return render(request, self.template_name,
                          {'schedule': Schedule.objects.filter(user_info_id=user_info.id)})
        else:
            user_info = UserInfo.objects.get(user_id=request.user.id)
            user_schedule = Schedule.objects.filter(user_info_id=user_info.id)
            for row in user_schedule:
                row.notification_status = row.notification_time < timezone.now()
                row.save()
            return render(request, self.template_name,
                          {'schedule': Schedule.objects.filter(user_info_id=user_info.id)})


class InputView(generic.DetailView):
    """A class that represents the input page view."""

    model = Intake
    template_name = 'aquaholic/input.html'

    def get(self, request, *args, **kwargs):
        """Input schedule page."""
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Input the amount of water from user and save to database."""
        try:
            amount = request.POST["amount"]
            date = request.POST["date"]
            # default time for intake date is 10 am
            intake_date = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(hours=10)
            aware_date = make_aware(intake_date)
            user_info = UserInfo.objects.get(user_id=request.user.id)
            # User already have intake for the given day, add amount of water to existed amount
            if Intake.objects.filter(user_info_id=user_info.id, date=aware_date).exists():
                intake = Intake.objects.get(user_info_id=user_info.id, date=aware_date)
                intake.total_amount += float(amount)
                intake.save()
            else:
                Intake.objects.create(user_info_id=user_info.id,
                                      date=intake_date,
                                      total_amount=amount)
            message = "Saved !"
            return render(request, self.template_name,
                          {'message': message})
        except ValueError:
            message = "Please, input in the field."
            return render(request, self.template_name,
                          {'message': message})


class HistoryView(generic.DetailView):
    """A class that represents the history page view."""

    model = Intake
    template_name = 'aquaholic/history.html'

    def show_history(self, request, selected_year, selected_month):
        """Get the data needed for history page and send those data as a context to history.html."""
        # count the number of days in the selected month
        num_days_in_month = calendar.monthrange(selected_year, selected_month)[1]

        # initialize a dictionary with date as a key and a list of amount, and bar color of the bar as a value
        all_amount_in_month = dict()
        for day in range(1, num_days_in_month + 1):
            all_amount_in_month[datetime.date(selected_year, selected_month, day).strftime("%d %b %Y")] = [0, "#d4f1f9"]

        # filter all intakes in selected month and year and update to the dictionary
        user_info = UserInfo.objects.get(user_id=request.user.id)
        goal = user_info.water_amount_per_day
        all_sorted_intakes = Intake.objects.filter(user_info_id=user_info.id,
                                                   date__month=selected_month,
                                                   date__year=selected_year).order_by('date')
        for intake in all_sorted_intakes:
            all_amount_in_month[intake.date.strftime("%d %b %Y")][0] = intake.total_amount
            if intake.total_amount < goal:
                # the bar color will be red if the amount doesn't reach the goal
                all_amount_in_month[intake.date.strftime("%d %b %Y")][1] = "#FF9999"
        return render(request, self.template_name, {"goal": goal,
                                                    "date": list(all_amount_in_month.keys()),
                                                    "amount": list(val[0] for val in all_amount_in_month.values()),
                                                    "recent_year": [datetime.datetime.now().year - i for i in range(5)],
                                                    "selected_month_int": selected_month,
                                                    "selected_month_str": datetime.date(2022, selected_month,
                                                                                        1).strftime('%b'),
                                                    "selected_year": selected_year,
                                                    "bar_colors": list(val[1] for val in all_amount_in_month.values())})

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
