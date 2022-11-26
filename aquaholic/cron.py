"""A method called by crontab."""
from .models import Schedule
from .notification import send_notification
from django.utils import timezone


def update_notification():
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
        if not user_info.notification_turned_on:
            for schedule in user_schedule:
                schedule.notification_time += timezone.timedelta(hours=24)
                schedule.notification_status = False
                schedule.save()
        else:
            for schedule in user_schedule:
                schedule.notification_time += timezone.timedelta(hours=24)
                schedule.save()
