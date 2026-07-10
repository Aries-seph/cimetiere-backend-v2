from django.db import models
from django.conf import settings
from caveaux.models import Caveau

# Create your models here.
class Reservation(models.Model):
    STATUS_CHOICES=(
        ("EN_ATTENTE",'En attente'),
        ("VALIDEE","Validée"),
        ("REFUSEE","Refusée"),
    )

    client = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="reservations"
)

    caveau=models.ForeignKey(
        Caveau,on_delete=models.CASCADE, related_name="reservations"
    )

    nom_defunt=models.CharField(max_length=255)
    date_deces=models.DateField()
    commentaire=models.TextField(blank=True)
    statut=models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="EN_ATTENTE"
    )
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} - {self.caveau.reference}"
class AuditLog(models.Model):
    ACTION_CHOICES = (
        ("VALIDATION", "Validation"),
        ("REFUS", "Refus"),
        ("CREATION", "Création"),
        ("MODIFICATION", "Modification"),
        ("SUPPRESSION", "Suppression"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs"
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    modele = models.CharField(max_length=30, blank=True)   # "Caveau", "Paiement", "Reservation"
    objet_id = models.CharField(max_length=50, blank=True)
    objet_repr = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"