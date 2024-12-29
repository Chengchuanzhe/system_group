# Generated by Django 3.0.4 on 2020-11-10 13:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homework',
            name='task',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='app01.Task'),
        ),
        migrations.AlterField(
            model_name='homework',
            name='user',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='app01.UserProfile'),
        ),
    ]