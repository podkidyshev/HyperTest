from django.contrib import admin

from .models import Test, Result, Question, Answer


class TestResultAdminInline(admin.TabularInline):
    model = Result


class TestQuestionAdminInline(admin.TabularInline):
    model = Question


class TestAdmin(admin.ModelAdmin):
    inlines = [TestResultAdminInline, TestQuestionAdminInline]


class AnswerInline(admin.TabularInline):
    model = Answer


class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]


admin.site.register(Test, TestAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Result)
