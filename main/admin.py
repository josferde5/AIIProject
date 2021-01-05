from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import Usuario, Genero, Editorial, Autor, Libro
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group

# Register your models here.


class UserCreateForm(UserCreationForm):

    class Meta:
        model = Usuario
        fields = ('username', 'genre')


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreateForm

    list_display = ('username', 'email', 'genre', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'genre')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'genre', 'password1', 'password2'),
        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'genre', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'genre')
    ordering = ('username',)
    filter_horizontal = ()


admin.site.register(Usuario, UserAdmin)
admin.site.register(Genero)
admin.site.register(Editorial)
admin.site.register(Autor)
admin.site.register(Libro)
admin.site.unregister(Group)
