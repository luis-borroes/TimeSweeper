# Generated by Django 2.2.7 on 2020-05-01 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sweeper', '0005_usermeeting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meeting',
            name='notes',
            field=models.CharField(max_length=500),
        ),
    ]
