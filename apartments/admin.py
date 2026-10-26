from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apartments.models import Apartment, User, Complains, Package

# Register your models here.
admin.site.register(Apartment)

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Apartment", {"fields": ("apartament",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Apartment", {"fields": ("apartament",)}),
    )
        
admin.site.register(User, CustomUserAdmin)
admin.site.register(Complains)
admin.site.register(Package)
