# Generated by Django 4.2.9 on 2025-02-15 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elearningapp', '0003_alter_coursematerial_material'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursematerial',
            name='document_name',
            field=models.CharField(default='p', max_length=256),
            preserve_default=False,
        ),
    ]
