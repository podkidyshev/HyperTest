# Generated by Django 3.0.4 on 2020-03-08 09:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=127, verbose_name='Title')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='Description')),
                ('picture', models.ImageField(blank=True, null=True, upload_to='tests', verbose_name='Picture')),
                ('published', models.BooleanField(default=False, verbose_name='Published')),
                ('vip', models.BooleanField(default=False, verbose_name='VIP')),
                ('price', models.IntegerField(default=0, verbose_name='Price')),
                ('gender', models.IntegerField(choices=[(0, 'Any'), (1, 'Male'), (2, 'Female')], default=0, verbose_name='For gender')),
            ],
            options={
                'verbose_name': 'Test',
                'verbose_name_plural': 'Tests',
                'db_table': 'test',
            },
        ),
        migrations.CreateModel(
            name='TestQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255, verbose_name='Текст')),
                ('picture', models.ImageField(blank=True, null=True, upload_to='tests-questions', verbose_name='Picture')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='main.Test', verbose_name='Test')),
            ],
            options={
                'verbose_name': 'Test question',
                'verbose_name_plural': 'Test questions',
                'db_table': 'test_question',
            },
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255, verbose_name='Текст')),
                ('picture', models.ImageField(blank=True, null=True, upload_to='tests-results', verbose_name='Picture')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='main.Test', verbose_name='Test')),
            ],
            options={
                'verbose_name': 'Test result',
                'verbose_name_plural': 'Test results',
                'db_table': 'test_result',
            },
        ),
        migrations.CreateModel(
            name='TestQuestionAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255, verbose_name='Текст')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='main.TestQuestion', verbose_name='Question')),
                ('result', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='answers', to='main.TestResult', verbose_name='Result')),
            ],
        ),
    ]
