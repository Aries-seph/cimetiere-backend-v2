from django.db import models
from django.conf import settings
from caveaux.models import Caveau
# Create your models here.


class Exhumation(models.Model):
    STATUT_CHOICES = (
        ("EN_ATTENTE", "En attente"),
        ("APPROUVEE", "Approuvée"),
        ("REFUSEE", "Refusée"),
        ("EFFECTUEE", "Effectuée"),
    )

    demandeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exhumations"
    )
    caveau = models.ForeignKey(
        Caveau,
        on_delete=models.CASCADE,
        related_name="exhumations"
    )
    nom_defunt = models.CharField(max_length=255)
    motif = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="EN_ATTENTE")
    date_demande = models.DateTimeField(auto_now_add=True)
    date_exhumation = models.DateField(null=True, blank=True)
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exhumations_approuvees"
    )
    observations = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom_defunt} - {self.caveau.reference} - {self.statut}"