import datetime

from .models import Schedule
from .notification import send_notification

import logging
logger = logging.getLogger(__name__)


def update_notification():
    logger = logging.getLogger(__name__)
    logger.debug("Cron job works")

    all_to_send = Schedule.objects.filter(notification_time__lte=datetime.datetime.now(),
                                          notification_status=False)
    for one_to_send in all_to_send:
        send_notification(f"Don't forget to drink {one_to_send.expected_amount:.2f} ml of water", one_to_send.user_info.notify_token)
        one_to_send.notification_status = True
        one_to_send.save()





