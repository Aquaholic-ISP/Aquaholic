# Generated by Django 4.1 on 2022-10-27 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aquaholic", "0009_alter_userinfo_water_amount_per_hour"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userinfo",
            name="water_amount_per_day",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
