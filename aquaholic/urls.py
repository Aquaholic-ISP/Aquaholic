from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "aquaholic"

urlpatterns = [
    path('noti/callback/', views.NotificationCallback.as_view(), name="callback"),
    path('aquaholic/<int:pk>/calculate', views.CalculateAuth.as_view(), name='calculate_auth'),
    path('aquaholic/<int:pk>/set_up', views.SetUp.as_view(), name='set_up'),
    path('aquaholic/<int:pk>/schedule', views.ScheduleView.as_view(), name='schedule'),

    path('aquaholic/', views.HomePage.as_view(), name='home'),
    path("", RedirectView.as_view(url="/aquaholic/")),
    path('aquaholic/calculate', views.Calculate.as_view(), name='calculate'),
    path('aquaholic/<int:pk>/input', views.Input.as_view(), name='input'),
    path('aquaholic/<int:pk>/history', views.History.as_view(), name='history'),
]
