from django.db import models
from django.conf import settings
from caveaux.models import Caveau

# Create your models here.

class Concession(models.Model):
    TYPE_CHOICES = (
        ("TEMPORAIRE", "Temporaire"),
        ("PERPETUELLE", "Perpétuelle"),
    )

    STATUT_CHOICES = (
        ("ACTIVE", "Active"),
        ("EXPIREE", "Expirée"),
        ("RESILIEE", "Résiliée"),
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="concessions"
    )
    caveau = models.ForeignKey(
        Caveau,
        on_delete=models.CASCADE,
        related_name="concessions"
    )
    type_concession = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="ACTIVE")
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)  # null si perpétuelle
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} - {self.caveau.reference} - {self.type_concession}"