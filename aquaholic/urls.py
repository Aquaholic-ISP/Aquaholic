from django.urls import path
from django.views.generic import RedirectView
from decouple import config
from django.views.generic import TemplateView

from . import views

app_name = "aquaholic"

line_notify_url = f"https://notify-bot.line.me/oauth/authorize?response_type=code&client_id={config('CLIENT_ID_NOTIFY')}" \
                    f"&redirect_uri={config('REDIRECT_URI_NOTIFY')}&scope=notify&state=testing123 "

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
    path('aquaholic/cron', views.update_notification, name='cron'),
    path('aquaholic/alert', views.login_alert, name='alert'),
    path('aquaholic/line-notify', views.LineNotifyVerificationView.as_view(), name="line-notify")
]
