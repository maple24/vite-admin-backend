# Generated by Django 4.1.1 on 2023-02-22 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0010_rename_published_time_task_publish_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='executor',
            name='scripts',
            field=models.TextField(blank=True, null=True),
        ),
    ]
