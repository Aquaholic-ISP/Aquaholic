from django.views import generic
from .models import UserInfo, Schedule, Intake, KILOGRAM_TO_POUND, OUNCES_TO_MILLILITER
from .notification import get_access_token, send_notification
from django.http import HttpResponseRedirect
from django.utils.timezone import make_aware
from django.shortcuts import render, reverse
import datetime
import calendar


def get_total_hours(first_notification_time, last_notification_time):
    """Calculate total hours from first and last notification time."""
    date = datetime.date(1, 1, 1)
    first_time = datetime.datetime.combine(date, first_notification_time)
    last_time = datetime.datetime.combine(date, last_notification_time)
    time = last_time - first_time
    return round(time.seconds / 3600)


class HomePage(generic.ListView):
    """A class that represents the home page view."""
    template_name = 'aquaholic/home.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        date = datetime.datetime.today().replace(hour=10, minute=0, second=0, microsecond=0)
        if user.is_authenticated:
            if not UserInfo.objects.filter(user_id=user.id).exists():
                UserInfo.objects.create(user_id=user.id)
            userinfo = UserInfo.objects.get(user_id=user.id)
            if Intake.objects.filter(user_info_id=userinfo.id, intake_date=date).exists():
                all_intake = Intake.objects.get(user_info_id=userinfo.id, intake_date=date)
                if all_intake:
                    goal = userinfo.water_amount_per_day
                    amount = int(all_intake.user_drinks_amount / goal * 100)
                    if amount <= 100:
                        return render(request, self.template_name, {"all_intake": f"{amount}"})
                    elif amount > 100:
                        amount = 100
                        return render(request, self.template_name, {"all_intake": f"{amount}"})
        return render(request, self.template_name)


class AboutUs(generic.ListView):
    """A class that represents the about us page view."""
    template_name = 'aquaholic/about_us.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class Calculate(generic.ListView):
    """A class that represents the calculation page view."""
    template_name = 'aquaholic/calculate.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request):
        try:
            weight = float(request.POST["weight"])
            exercise_time = float(request.POST["exercise_time"])
            water_amount_per_day = ((weight * KILOGRAM_TO_POUND * 0.5)
                                    + (exercise_time / 30) * 12) * OUNCES_TO_MILLILITER
            return render(request, self.template_name,
                          {'result': f"{water_amount_per_day:.2f}"})
        except ValueError:
            message = "Please, enter a positive number in both fields."
            return render(request, self.template_name,
                          {'message': message})


class CalculateAuth(generic.DetailView):
    """A class that represents the calculation page view for authenticate user."""
    template_name = 'aquaholic/calculation_auth.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'user': request.user})

    def post(self, request, *args, **kwargs):
        try:
            user_info = UserInfo.objects.get(user_id=request.user.id)
            user_info.weight = float(request.POST["weight"])
            user_info.exercise_time = float(request.POST["exercise_time"])
            user_info.water_amount_per_day = ((user_info.weight * KILOGRAM_TO_POUND * 0.5)
                                              + (user_info.exercise_time / 30) * 12) * OUNCES_TO_MILLILITER
            user_info.get_water_amount_per_hour()
            user_info.save()

            all_schedules = Schedule.objects.filter(user_info_id=user_info.id)
            for one_schedule in all_schedules:
                one_schedule.expected_amount = round(user_info.water_amount_per_hour, 2)
                one_schedule.save()
            return render(request, self.template_name,
                          {'result': f"{user_info.water_amount_per_day:.2f}"})
        except ValueError:
            message = "Please, enter a positive number in both fields."
            return render(request, self.template_name,
                          {'message': message})


class SetUp(generic.DetailView):
    """A class that represents the set up page view."""
    template_name = 'aquaholic/set_up.html'

    def get(self, request, *args, **kwargs):
        # user who have already generate token doesn't have to generate token
        return render(request, self.template_name, {'user': request.user})

    def post(self, request, *args, **kwargs):
        token_exist = False
        token = UserInfo.objects.get(user_id=request.user.id).notify_token
        if token is not None:
            token_exist = True
        try:
            first = request.POST["first_notification"]
            last = request.POST["last_notification"]
            first_notify_time = datetime.datetime.strptime(first, "%H:%M").time()
            last_notify_time = datetime.datetime.strptime(last, "%H:%M").time()
            if first == last or get_total_hours(first_notify_time, last_notify_time) == 0:
                message = "Please, enter different time or time difference is more than 1 hour."
                return render(request, self.template_name,
                              {'message': message})
            user = UserInfo.objects.get(user_id=request.user.id)
            user.first_notification_time = first_notify_time
            user.last_notification_time = last_notify_time
            user.save()

            user = request.user
            userinfo = UserInfo.objects.get(user_id=user.id)
            # calculate and save total hours and water amount per hour to database
            userinfo.total_hours = get_total_hours(userinfo.first_notification_time,
                                                   userinfo.last_notification_time)
            userinfo.get_water_amount_per_hour()
            userinfo.save()

            # get total hours, first notification time and expected amount (water amount to dink per hour)
            total_hours = int(userinfo.total_hours)
            first_notify_time = userinfo.first_notification_time
            expected_amount = userinfo.water_amount_per_hour

            first_notification_time = datetime.datetime.combine(datetime.date.today(), first_notify_time)
            last_notification_time = first_notification_time + datetime.timedelta(hours=total_hours)

            # user already have schedule
            if Schedule.objects.filter(user_info_id=userinfo.id).exists():
                found_schedule = Schedule.objects.filter(user_info_id=userinfo.id)
                for one_schedule in found_schedule:
                    one_schedule.delete()
            # create schedule
            if last_notification_time < datetime.datetime.now():
                first_notification_time += datetime.timedelta(hours=24)
            for i in range(total_hours+1):
                Schedule.objects.create(user_info_id=userinfo.id,
                                        notification_time=first_notification_time,
                                        expected_amount=round(expected_amount, 2),
                                        notification_status=(first_notification_time < datetime.datetime.now()),
                                        is_last=(i == total_hours)
                                        )
                first_notification_time += datetime.timedelta(hours=1)
            if token_exist:
                return HttpResponseRedirect(reverse('aquaholic:schedule', args=(user.id,)))
            else:
                url = "https://notify-bot.line.me/oauth/authorize?response_type=code&client_id=fVKMI2Q1k3MY5D3w2g0Hwt&redirect_uri=http://127.0.0.1:8000/noti/callback/&scope=notify&state=testing123"
                return HttpResponseRedirect(url)
        except:
            message = "Please, enter time in both fields."
            return render(request, self.template_name,
                          {'message': message})


class NotificationCallback(generic.DetailView):
    """A class that handles the callback after user authorize notification."""

    def get(self, request, *args, **kwargs):
        """Send welcome message to new user."""
        code = request.GET['code']
        token = get_access_token(code)
        send_notification("Welcome to aquaholic", token)
        user = UserInfo.objects.get(user_id=request.user.id)
        user.notify_token = token
        user.save()
        return HttpResponseRedirect(reverse('aquaholic:schedule', args=(request.user.id,)))


class ScheduleView(generic.DetailView):
    model = Schedule
    template_name = 'aquaholic/schedule.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        userinfo = UserInfo.objects.get(user_id=user.id)
        return render(request, self.template_name,
                      {'schedule': Schedule.objects.filter(user_info_id=userinfo.id)})


class Input(generic.DetailView):
    """A class that represents the input page view."""
    model = Intake
    template_name = 'aquaholic/input.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'user': request.user})
    
    def post(self, request, *args, **kwargs):
        try:
            amount = request.POST["amount"]
            date = request.POST["date"]
            intake_date = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(hours=10)
            aware_date = make_aware(intake_date)
            userinfo = UserInfo.objects.get(user_id=request.user.id)
            if Intake.objects.filter(user_info_id=userinfo.id, intake_date=aware_date).exists():
                intake = Intake.objects.get(user_info_id=userinfo.id, intake_date=aware_date)
                intake.user_drinks_amount += float(amount)
                intake.save()
            else:
                Intake.objects.create(user_info_id=userinfo.id,
                                      intake_date=intake_date,
                                      user_drinks_amount=amount)
            return HttpResponseRedirect(reverse('aquaholic:home'))
        except:
            message = "Please, input in the field."
            return render(request, self.template_name,
                          {'message': message})


def get_five_recent_years():
    this_year = datetime.datetime.now().year
    return [this_year-i for i in range(5)]


class History(generic.DetailView):
    """A class that represents the history page view."""
    model = Intake
    template_name = 'aquaholic/history.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        userinfo = UserInfo.objects.get(user_id=user.id)
        all_intake = Intake.objects.filter(user_info_id=userinfo.id)
        sorted_intakes = all_intake.order_by('intake_date')

        today = datetime.datetime.now()
        this_month = today.month
        this_year = today.year
        num_days = calendar.monthrange(this_year, this_month)[1]
        days = dict()
        for day in range(1, num_days+1):
            days[datetime.date(this_year, this_month, day).strftime("%d %b %Y")] = 0

        for intake in sorted_intakes:
            intake_date = intake.intake_date
            intake_date_month = intake_date.month
            intake_date_year = intake_date.year
            if (this_month == intake_date_month) and (this_year == intake_date_year):
                days[intake_date.strftime("%d %b %Y")] = intake.user_drinks_amount
        return render(request, self.template_name, {"all_intake": all_intake,
                                                    "goal": userinfo.water_amount_per_day,
                                                    "date": list(days.keys()),
                                                    "amount": list(days.values()),
                                                    "recent_year": get_five_recent_years(),
                                                    "selected_month_int": this_month,
                                                    "selected_month_str": today.strftime("%b")})

    def post(self, request, *args, **kwargs):
        user = request.user
        userinfo = UserInfo.objects.get(user_id=user.id)
        all_intake = Intake.objects.filter(user_info_id=userinfo.id)
        sorted_intakes = all_intake.order_by('intake_date')

        selected_month = int(request.POST['month'])
        selected_year = int(request.POST['year'])
        num_days = calendar.monthrange(selected_year, selected_month)[1]

        days = dict()
        for day in range(1, num_days + 1):
            days[datetime.date(selected_year, selected_month, day).strftime("%d %b %Y")] = 0

        for intake in sorted_intakes:
            intake_date = intake.intake_date
            intake_date_month = intake_date.month
            intake_date_year = intake_date.year
            if (selected_month == intake_date_month) and (selected_year == intake_date_year):
                days[intake_date.strftime("%d %b %Y")] = intake.user_drinks_amount
        return render(request, self.template_name, {"all_intake": all_intake,
                                                    "goal": userinfo.water_amount_per_day,
                                                    "date": list(days.keys()),
                                                    "amount": list(days.values()),
                                                    "recent_year": get_five_recent_years(),
                                                    "selected_month_int": selected_month,
                                                    "selected_month_str": datetime.date(2022, selected_month, 1).strftime('%b')})
