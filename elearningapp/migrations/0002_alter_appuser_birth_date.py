# Generated by Django 4.2.9 on 2025-02-15 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elearningapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appuser',
            name='birth_date',
            field=models.DateField(),
        ),
    ]
