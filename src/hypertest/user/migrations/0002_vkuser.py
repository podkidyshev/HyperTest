# Generated by Django 3.0.4 on 2020-03-22 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VKUser',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False, verbose_name='VK ID')),
                ('coins', models.IntegerField(default=0, verbose_name='Coins count')),
            ],
            options={
                'verbose_name': 'VK user',
                'verbose_name_plural': 'VK users',
                'db_table': 'vk_user',
            },
        ),
    ]
