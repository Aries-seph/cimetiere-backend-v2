from django.contrib import admin
from .models import Reservation
from .models import Reservation, AuditLog

# Register your models here.
admin.site.register(Reservation)
admin.site.register(AuditLog)