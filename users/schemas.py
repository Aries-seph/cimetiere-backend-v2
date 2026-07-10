# users/schemas.py
from ninja import Schema
from pydantic import EmailStr
from typing import Optional


class LoginRequestSchema(Schema):
    """Schéma pour la demande de connexion."""
    email: EmailStr
    password: str


class LogoutRequestSchema(Schema):
    """Schéma pour la demande de déconnexion."""
    refresh: str


class MFAVerifyRequestSchema(Schema):
    """Schéma pour la vérification MFA."""
    email: EmailStr
    code: str


class UserProfileUpdateSchema(Schema):
    """Schéma pour la mise à jour du profil."""
    username: Optional[str] = None
    telephone: Optional[str] = None


class RegisterRequestSchema(Schema):
    """Schéma pour l'inscription."""
    username: str
    email: EmailStr
    password: str
    telephone: Optional[str] = None