# finances/schemas.py
from ninja import Schema
from typing import Optional


class PaiementCreateSchema(Schema):
    """Schéma pour la création d'un paiement."""
    reservation_id: int
    montant: float
    canal: str


class PaiementResponseSchema(Schema):
    """Schéma de réponse pour un paiement."""
    id: int
    reservation_id: int
    montant: float
    canal: str
    statut: str
    reference: str
    created_at: str