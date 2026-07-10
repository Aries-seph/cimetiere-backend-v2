from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets=UserAdmin.fieldsets + (("Informations supplémentaires",
                                     {
                                      "fields":("telephone","role","mfa_active") , 
                                     }),
    )

    add_fieldsets=UserAdmin.add_fieldsets + (
                                            ("Informations supplémentaires",{
                                      "fields":("telephone","role","mfa_active") , 
                                            }),
    )

    list_display=("username","email","role","is_staff","is_active")