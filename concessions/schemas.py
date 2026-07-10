# concessions/schemas.py
from ninja import Schema
from typing import Optional
from datetime import date


class ConcessionCreateSchema(Schema):
    """Schéma pour la création d'une concession."""
    client_id: int
    caveau_id: int
    type_concession: str
    date_debut: date
    date_fin: Optional[date] = None


class ConcessionResponseSchema(Schema):
    """Schéma de réponse pour une concession."""
    id: int
    caveau_id: int
    type_concession: str
    statut: str
    date_debut: date
    date_fin: Optional[date] = None