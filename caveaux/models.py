from django.db import models

# Create your models here.
class Section(models.Model):
    nom=models.CharField(max_length=100)
    description=models.CharField(blank=True)

    def __str__(self):
        return self.nom
    
class Bloc(models.Model):
    section=models.ForeignKey(
        Section,on_delete=models.CASCADE, related_name="blocs"
    )

    nom=models.CharField(max_length=100)

    def __str__(self):
        return f"{self.section.nom} - {self.nom}"
    
class Caveau(models.Model):
    STATUS_CHOICE=(
        ("DISPONIBLE","Disponible"),
        ("RESERVE","Réservé"),
        ("OCCUPE","Occupé"),
        ("INEXPLOITABLE","Inexploitable"),
    )

    bloc=models.ForeignKey(
        Bloc,on_delete=models.CASCADE,related_name="caveaux"
    )

    reference=models.CharField(max_length=50,unique=True)
    longueur=models.FloatField()
    largeur=models.FloatField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    statut=models.CharField(
        max_length=20, choices=STATUS_CHOICE,default="DISPONIBLE"
    )

    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference
