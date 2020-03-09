from django.contrib import admin

from .models import Test, Result, Question


class TestResultAdminInline(admin.TabularInline):
    model = Result


class TestQuestionAdminInline(admin.TabularInline):
    model = Question


class TestAdmin(admin.ModelAdmin):
    inlines = [TestResultAdminInline, TestQuestionAdminInline]


admin.site.register(Test, TestAdmin)
