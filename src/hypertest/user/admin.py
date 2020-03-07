from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext as _

from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'is_admin']


class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = (
        (None, {'fields': ('username', 'password', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_admin'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_admin')}
         ),
    )

    list_display = ('username', 'email', 'is_admin')
    list_filter = ('is_admin', 'is_active')
    search_fields = ('username', 'email')
    filter_horizontal = []
    ordering = ('-id',)

    add_form = CustomUserCreationForm


admin.site.register(User, CustomUserAdmin)
