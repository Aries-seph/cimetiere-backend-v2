from django.contrib.auth.models import AbstractUser
from django.db import models
import random
from django.utils import timezone
from datetime import timedelta
# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES=(
        ('ADMIN','Administrateur'),
        ('AGENT','Agent'),
        ('SECRETARIAT','Secrétariat'),
        ('CLIENT','Client'),
    )

    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    telephone=models.CharField(max_length=20,blank=True)
    role=models.CharField(max_length=25,choices=ROLE_CHOICES,default='CLIENT')
    mfa_active=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    last_profile_update = models.DateTimeField(null=True, blank=True)
    pending_pick_lat = models.FloatField(null=True, blank=True)
    pending_pick_lng = models.FloatField(null=True, blank=True)
    pending_pick_caveau_id = models.IntegerField(null=True, blank=True)
    def __str__(self):
        return self.username
    

class MFACode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        expiry = self.created_at + timedelta(minutes=10)
        return not self.is_used and timezone.now() < expiry

    @classmethod
    def generate_for(cls, user):
        cls.objects.filter(user=user, is_used=False).delete()
        code = str(random.randint(100000, 999999))
        return cls.objects.create(user=user, code=code)

    def __str__(self):
        return f"{self.user.email} - {self.code}"

