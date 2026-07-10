from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import   Reservation

@receiver(post_save,sender=Reservation)
def update_caveau_status(sender,instance,**kwargs):
    if instance.statut=="VALIDEE":
        caveau=instance.caveau
        caveau.statut="OCCUPE"
        caveau.save()