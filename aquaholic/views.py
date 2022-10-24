from django.views import generic
from .models import UserInfo, Schedule, Intake
from django.shortcuts import render
from .models import UserInfo, KILOGRAM_TO_POUND, OUNCES_TO_MILLILITER


class HomePage(generic.ListView):
    """A class that represents the home page view."""
    template_name = 'aquaholic/home.html'

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


class SetUp(generic.DetailView):
    """A class that represents the set up page view."""
    template_name = 'aquaholic/set_up.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class Progress(generic.DetailView):
    """A class that represents the progress page view."""
    model = Schedule
    template_name = 'aquaholic/progress.html'


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
