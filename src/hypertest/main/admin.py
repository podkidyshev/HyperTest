from django.contrib import admin

from .models import Test, TestResult, TestQuestion


class TestResultAdminInline(admin.TabularInline):
    model = TestResult


class TestQuestionAdminInline(admin.TabularInline):
    model = TestQuestion


class TestAdmin(admin.ModelAdmin):
    inlines = [TestResultAdminInline, TestQuestionAdminInline]


admin.site.register(Test, TestAdmin)
