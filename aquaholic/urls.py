from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "aquaholic"

urlpatterns = [
    path('noti/callback/', views.NotificationCallbackView.as_view(), name="callback"),
    path('aquaholic/<int:pk>/calculate', views.CalculateAuthView.as_view(), name='calculate_auth'),
    path('aquaholic/<int:pk>/set_up', views.SetUpView.as_view(), name='set_up'),
    path('aquaholic/<int:pk>/schedule', views.ScheduleView.as_view(), name='schedule'),
    path('aquaholic/<int:pk>/registration', views.RegistrationView.as_view(), name='registration'),

    path('aquaholic/', views.HomePageView.as_view(), name='home'),
    path("", RedirectView.as_view(url="/aquaholic/")),
    path('aquaholic/calculate', views.CalculateView.as_view(), name='calculate'),
    path('aquaholic/<int:pk>/input', views.InputView.as_view(), name='input'),
    path('aquaholic/<int:pk>/history', views.HistoryView.as_view(), name='history'),
    path('aquaholic/about_us', views.AboutUsView.as_view(), name='about_us'),
    path('aquaholic/profile', views.ProfileView.as_view(), name="profile"),
]
