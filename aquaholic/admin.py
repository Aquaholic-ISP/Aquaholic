from django.contrib import admin
from .models import UserInfo, Schedule, Intake


class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'weight',
                    'exercise_time',
                    'water_amount_per_day',
                    'first_notification_time',
                    'last_notification_time',
                    'total_hours',
                    'water_amount_per_hour',
                    'notify_token',
                    )
    list_filter = ['user',
                    'weight',
                    'exercise_time',
                    'water_amount_per_day',
                    'first_notification_time',
                    'last_notification_time',
                    'total_hours',
                    'water_amount_per_hour',
                    'notify_token',
                   ]
    search_fields = ['user']


class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('user_info',
                    'notification_time',
                    'expected_amount',
                    'notification_status',
                    )
    list_filter = ['user_info',
                    'notification_time',
                    'expected_amount',
                    'notification_status',
                   ]
    search_fields = ['user_info']


class IntakeAdmin(admin.ModelAdmin):
    list_display = ('user_info',
                    'user_drinks_amount',
                    'intake_date',
                    )

    list_filter = ['user_info',
                   'user_drinks_amount',
                   'intake_date',
                   ]
    search_fields = ['user_info']


admin.site.register(UserInfo, UserInfoAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Intake, IntakeAdmin)
