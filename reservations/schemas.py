# reservations/schemas.py
from ninja import Schema
from typing import Optional
from datetime import date


class ReservationCreateSchema(Schema):
    """Schéma pour la création d'une réservation."""
    caveau_id: int
    nom_defunt: str
    date_deces: date
    commentaire: Optional[str] = None


class ReservationResponseSchema(Schema):
    """Schéma de réponse pour une réservation."""
    id: int
    caveau_id: int
    nom_defunt: str
    date_deces: date
    statut: str
    commentaire: Optional[str] = None
    created_at: str