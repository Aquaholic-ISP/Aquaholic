from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aquaholic", "0014_rename_schedulemodel_schedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedule",
            name="is_last",
            field=models.BooleanField(default=False),
        ),
    ]
