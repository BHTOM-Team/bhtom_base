from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from bhtom_custom_registration.bhtom_registration.models import LatexUser
from django.contrib.auth.models import User

class UserLatexInline(admin.StackedInline):
    model = LatexUser
    list_display = ['lalatex_name', 'latex_affiliation','address','about_me','orcid_id']


class CustomUserAdmin(UserAdmin):
    inlines = [UserLatexInline]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)