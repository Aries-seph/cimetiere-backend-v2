# caveaux/schemas.py
from typing import Optional
from ninja import Schema
from pydantic import field_validator


class CaveauCreateSchema(Schema):
    """Schéma pour la création d'un caveau."""
    bloc_id: int
    reference: str
    longueur: float
    largeur: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("La latitude doit être comprise entre -90 et 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("La longitude doit être comprise entre -180 et 180")
        return v


class CaveauResponseSchema(Schema):
    """Schéma de réponse pour un caveau."""
    id: int
    reference: str
    longueur: float
    largeur: float
    statut: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bloc_id: int


class CaveauUpdateSchema(Schema):
    """Schéma pour la mise à jour d'un caveau."""
    reference: Optional[str] = None
    longueur: Optional[float] = None
    largeur: Optional[float] = None
    statut: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("La latitude doit être comprise entre -90 et 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("La longitude doit être comprise entre -180 et 180")
        return v