# exhumations/schemas.py
from ninja import Schema
from typing import Optional
from datetime import date


class ExhumationCreateSchema(Schema):
    """Schéma pour la création d'une exhumation."""
    caveau_id: int
    nom_defunt: str
    motif: str
    date_exhumation: Optional[date] = None


class ExhumationUpdateSchema(Schema):
    """Schéma pour la mise à jour d'une exhumation."""
    observations: Optional[str] = None
    date_exhumation: Optional[date] = None