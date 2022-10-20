from django.views import generic
from .models import UserInfo, Schedule, Intake


class HomePage(generic.ListView):
    """A class that represents the home page view."""
    model = UserInfo
    template_name = 'aquaholic/home.html'


class Calculate(generic.ListView):
    """A class that represents the home page view."""
    model = UserInfo
    template_name = 'aquaholic/calculate.html'


class SetUp(generic.DetailView):
    """A class that represents the set up page view."""
    model = UserInfo
    template_name = 'aquaholic/set_up.html'


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
