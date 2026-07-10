from django.db import models
from django.conf import settings
from reservations.models import Reservation

# Create your models here.

class Paiement(models.Model):
    CANAL_CHOICES = (
        ("MOBILE_MONEY", "Mobile Money"),
        ("AIRTEL_MONEY", "Airtel Money"),
        ("ESPECES", "Espèces"),
        ("VIREMENT", "Virement"),
    )

    STATUT_CHOICES = (
        ("EN_ATTENTE", "En attente"),
        ("VALIDE", "Validé"),
        ("REFUSE", "Refusé"),
    )

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="paiements"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paiements"
    )
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_ATTENTE")
    reference = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} - {self.montant} - {self.canal}"