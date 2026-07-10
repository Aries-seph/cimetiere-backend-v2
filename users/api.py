# users/api.py (extrait des endpoints principaux)
from ninja import Router
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from users.schemas import (
    LoginRequestSchema, LogoutRequestSchema, MFAVerifyRequestSchema,
    RegisterRequestSchema, UserProfileUpdateSchema
)
from users.auth import JWTAuth
from users.models import User, MFACode
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any

router = Router()
auth = JWTAuth()


def _send_mfa_code(user: User) -> MFACode:
    """Génère et envoie un code MFA à l'utilisateur."""
    mfa = MFACode.generate_for(user)
    send_mail(
        subject='Votre code de connexion',
        message=f'Bonjour {user.username},\n\nVotre code de connexion est : {mfa.code}\n\nCe code expire dans 10 minutes.',
        from_email='jeremykounkou@icloud.com',
        recipient_list=[user.email],
    )
    return mfa


@router.post("/register")
def register_new_user(request, data: RegisterRequestSchema) -> Dict[str, Any]:
    """Inscription d'un nouvel utilisateur."""
    
    if User.objects.filter(email=data.email).exists():
        return {"success": False, "message": "Un compte existe déjà avec cet email"}
    
    if User.objects.filter(username=data.username).exists():
        return {"success": False, "message": "Ce nom d'utilisateur est déjà pris"}
    
    if len(data.password) < 8:
        return {"success": False, "message": "Le mot de passe doit contenir au moins 8 caractères"}
    
    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        telephone=data.telephone or "",
        role="CLIENT",
    )
    
    return {"success": True, "message": "Compte créé avec succès"}


@router.post("/login")
def login_user(request, data: LoginRequestSchema) -> Dict[str, Any]:
    """Authentification de l'utilisateur."""
    user = authenticate(
        request,
        username=data.email,
        password=data.password
    )
    
    if not user:
        return {"success": False, "message": "Identifiants incorrects"}
    
    _send_mfa_code(user)
    
    return {
        "success": True,
        "mfa_required": True,
        "message": "Un code a été envoyé à votre adresse email"
    }


@router.post("/verify-mfa")
def verify_mfa_code(request, data: MFAVerifyRequestSchema) -> Dict[str, Any]:
    """Vérification du code MFA."""
    
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return {"success": False, "message": "Utilisateur introuvable"}
    
    mfa = MFACode.objects.filter(
        user=user,
        code=data.code,
        is_used=False
    ).last()
    
    if not mfa or not mfa.is_valid():
        return {"success": False, "message": "Code invalide ou expiré"}
    
    mfa.is_used = True
    mfa.save()
    
    refresh = RefreshToken.for_user(user)
    
    return {
        "success": True,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }


@router.get("/me", auth=auth)
def get_current_user_profile(request) -> Dict[str, Any]:
    """Récupère le profil de l'utilisateur connecté."""
    user = request.auth
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "telephone": user.telephone,
        "mfa_active": user.mfa_active,
    }


@router.patch("/me", auth=auth)
def update_current_user_profile(request, data: UserProfileUpdateSchema) -> Dict[str, Any]:
    """Met à jour le profil de l'utilisateur connecté."""
    user = request.auth
    
    if user.last_profile_update:
        elapsed = timezone.now() - user.last_profile_update
        if elapsed < timedelta(hours=48):
            remaining_hours = 48 - int(elapsed.total_seconds() // 3600)
            return {
                "success": False,
                "message": f"Vous devez attendre encore environ {remaining_hours}h avant de pouvoir modifier vos informations à nouveau."
            }
    
    changes = []
    update_data = data.dict(exclude_unset=True, exclude_none=True)
    
    for key, value in update_data.items():
        old_value = getattr(user, key)
        if old_value != value:
            changes.append(f"{key} : '{old_value}' → '{value}'")
            setattr(user, key, value)
    
    if not changes:
        return {"success": False, "message": "Aucune modification détectée"}
    
    user.last_profile_update = timezone.now()
    user.save()
    
    admins = User.objects.filter(role="ADMIN").values_list("email", flat=True)
    
    if admins:
        send_mail(
            subject="Modification de profil utilisateur",
            message=f"L'utilisateur {user.username} ({user.email}) a modifié son profil :\n\n" + "\n".join(changes),
            from_email='jeremykounkou@icloud.com',
            recipient_list=list(admins),
        )
    
    return {"success": True, "message": "Profil mis à jour"}


@router.post("/logout", auth=auth)
def logout_user(request, data: LogoutRequestSchema) -> Dict[str, Any]:
    """Déconnexion de l'utilisateur."""
    try:
        token = RefreshToken(data.refresh)
        token.blacklist()
        return {"success": True, "message": "Déconnecté"}
    except TokenError:
        return {"success": False, "message": "Token invalide ou déjà expiré"}


@router.get("/pending-pick", auth=auth)
def get_pending_location_pick(request) -> Dict[str, Any]:
    """Récupère et efface les coordonnées en attente."""
    user = request.auth
    
    if user.pending_pick_lat is None:
        return {"has_pick": False}
    
    data = {
        "has_pick": True,
        "latitude": user.pending_pick_lat,
        "longitude": user.pending_pick_lng,
        "caveau_id": user.pending_pick_caveau_id,
    }
    
    user.pending_pick_lat = None
    user.pending_pick_lng = None
    user.pending_pick_caveau_id = None
    user.save()
    
    return data