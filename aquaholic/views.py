from django.views import generic
from .models import UserInfo, Schedule, Intake
from django.shortcuts import render, reverse, redirect
from .models import UserInfo, KILOGRAM_TO_POUND, OUNCES_TO_MILLILITER
from .notification import get_access_token, send_notification
from django.http import HttpResponseRedirect
import datetime
from decimal import Decimal


class HomePage(generic.ListView):
    """A class that represents the home page view."""
    template_name = 'aquaholic/home.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if not UserInfo.objects.filter(user_id=user.id).exists():
                UserInfo.objects.create(user_id=user.id)
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

        w = request.POST["weight"]
        t = request.POST["exercise_time"]
        weight = Decimal(request.POST["weight"]).quantize(Decimal('1.00'))
        exercise_time = Decimal(request.POST["exercise_time"]).quantize(Decimal('1.00'))
        water_amount_per_day = ((float(w) * KILOGRAM_TO_POUND * 0.5)
                                + (float(t) / 30) * 12) * OUNCES_TO_MILLILITER
        wp = Decimal(water_amount_per_day).quantize(Decimal('1.00'))
        user = UserInfo.objects.get(user_id=request.user.id)
        user.weight = weight
        user.exercise_time = exercise_time
        user.water_amount_per_day = wp
        user.save()
        return render(request, self.template_name,
                      {'result': f"{wp:.2f}"})


class SetUp(generic.DetailView):
    """A class that represents the set up page view."""
    template_name = 'aquaholic/set_up.html'

    def get(self, request, *args, **kwargs):
        # TODO receive first notification time and last notification time from user and save to database

        try:
            # user who have already generate token doesn't have to generate token
            token = UserInfo.objects.get(user_id=request.user.id).notify_token
            return render(request, self.template_name,
                          {'token_exist': True,
                           'user': request.user})
        except:
            # user already generate token
            return render(request, self.template_name,
                          {'token_exist': False,
                           'user': request.user})


class NotificationCallback(generic.DetailView):
    """A class that represents the progress page view."""

    def get(self, request, *args, **kwargs):
        """Send welcome message to new user."""
        token = get_access_token(request.GET['code'])
        send_notification("Welcome to aquaholic", token)


        w = decimal.Decimal(50.32)
        t = decimal.Decimal(60.32)
        UserInfo.objects.create(weight=decimal.Decimal(50.32),
                               exercise_time=decimal.Decimal(60.32),
                               first_notification_time=datetime.time(8, 0, 0),
                               last_notification_time=datetime.time(22, 0, 0)
                                )
        return HttpResponseRedirect(reverse('aquaholic:schedule', args=(request.user.id,)))


class ScheduleView(generic.DetailView):
    model = Schedule
    template_name = 'aquaholic/schedule.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class Input(generic.DetailView):
    """A class that represents the input page view."""
    model = Intake
    template_name = 'aquaholic/input.html'


class History(generic.DetailView):
    """A class that represents the history page view."""
    model = Intake
    template_name = 'aquaholic/history.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
