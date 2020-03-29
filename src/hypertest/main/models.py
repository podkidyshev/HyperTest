from django.db import models
from django.utils.translation import ugettext as _

from hypertest.user.models import VKUser


class GenderChoices(models.IntegerChoices):
    ANY = 0, 'Any'
    MALE = 1, 'Male'
    FEMALE = 2, 'Female'


class Test(models.Model):
    title = models.CharField(_('Title'), max_length=127)
    description = models.CharField(_('Description'), max_length=255, blank=True, null=True)
    picture = models.ImageField(_('Picture'), blank=True, null=True, upload_to='tests')

    published = models.BooleanField(_('Published'), default=False)
    vip = models.BooleanField(_('VIP'), default=False)
    price = models.IntegerField(_('Price'), default=0)
    gender = models.IntegerField(_('For gender'), choices=GenderChoices.choices, default=GenderChoices.ANY)

    user = models.ForeignKey(VKUser, on_delete=models.SET_NULL, related_name='tests', verbose_name=_('Creator'),
                             blank=True, null=True)

    class Meta:
        db_table = 'test'
        verbose_name = _('Test')
        verbose_name_plural = _('Tests')


class Result(models.Model):
    result_id = models.IntegerField(_('Result ID'))
    test = models.ForeignKey(verbose_name=_('Test'), to=Test, on_delete=models.CASCADE, related_name='results')
    text = models.CharField(_('Text'), max_length=255)
    description = models.CharField(_('Description'), max_length=255, blank=True, null=True)
    picture = models.ImageField(_('Picture'), blank=True, null=True, upload_to='tests-results')

    class Meta:
        db_table = 'test_result'
        verbose_name = _('Test result')
        verbose_name_plural = _('Test results')

        unique_together = [['result_id', 'test']]


class Question(models.Model):
    question_id = models.IntegerField(_('Question ID'))
    test = models.ForeignKey(verbose_name=_('Test'), to=Test, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(_('Text'), max_length=255)
    picture = models.ImageField(_('Picture'), blank=True, null=True, upload_to='tests-questions')

    class Meta:
        db_table = 'test_question'
        verbose_name = _('Test question')
        verbose_name_plural = _('Test questions')

        unique_together = [['question_id', 'test']]


class Answer(models.Model):
    answer_id = models.IntegerField(_('Question Answer ID'))
    question = models.ForeignKey(verbose_name=_('Question'), to=Question, related_name='answers',
                                 on_delete=models.CASCADE)
    result = models.ForeignKey(verbose_name=_('Result'), to=Result, related_name='answers',
                               on_delete=models.SET_NULL, blank=True, null=True)
    text = models.CharField(_('Text'), max_length=255)

    class Meta:
        db_table = 'test_question_answer'
        verbose_name = _('Test question answer')
        verbose_name_plural = _('Test question answers')

        unique_together = [['answer_id', 'question']]
