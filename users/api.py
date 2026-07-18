# users/api.py
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
from typing import Dict, Any, List
from cimetiere.brevo import send_brevo_email
import logging

logger = logging.getLogger(__name__)

router = Router()
auth = JWTAuth()


@router.post("/register")
def register_new_user(request, data: RegisterRequestSchema) -> Dict[str, Any]:
    """Inscription d'un nouvel utilisateur."""
    
    print("🔵 ===== REGISTER =====")
    print(f"🔵 Email: {data.email}")
    print(f"🔵 Username: {data.username}")
    
    if User.objects.filter(email=data.email).exists():
        print("🔴 Email déjà utilisé")
        return {"success": False, "message": "Un compte existe déjà avec cet email"}
    
    if User.objects.filter(username=data.username).exists():
        print("🔴 Username déjà pris")
        return {"success": False, "message": "Ce nom d'utilisateur est déjà pris"}
    
    if len(data.password) < 8:
        print("🔴 Mot de passe trop court")
        return {"success": False, "message": "Le mot de passe doit contenir au moins 8 caractères"}
    
    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        telephone=data.telephone or "",
        role="CLIENT",
    )
    
    print(f"✅ Utilisateur créé: {user.email} (ID: {user.id})")
    print("🔵 ===== FIN REGISTER =====")
    
    return {"success": True, "message": "Compte créé avec succès"}


@router.post("/login")
def login_user(request, data: LoginRequestSchema) -> Dict[str, Any]:
    """
    Authentification de l'utilisateur et génération/envoi du code MFA.
    """
    print("🔵 ===== LOGIN =====")
    print(f"🔵 Email: {data.email}")
    
    # 1. Valider les identifiants via Django Auth
    user = authenticate(request, username=data.email, password=data.password)
    if not user:
        print("🔴 Identifiants incorrects")
        return {"success": False, "message": "Identifiants incorrects"}

    print(f"🔵 Utilisateur trouvé: {user.email} (ID: {user.id})")

    # 2. Générer le code MFA dans votre table Supabase
    try:
        mfa = MFACode.generate_for(user)
        code = mfa.code
        print(f"🔵 Code MFA généré: {code}")
    except Exception as e:
        print(f"🔴 Erreur génération MFA: {e}")
        import random
        code = f"{random.randint(100000, 999999)}"
        mfa = MFACode.objects.create(user=user, code=code)
        print(f"🔵 Code MFA créé manuellement: {code}")

    # 3. Envoyer l'email par l'API HTTP Brevo
    print(f"🔵 Envoi de l'email à {user.email}")
    email_sent = send_brevo_email(
        to_email=user.email,
        subject="🔐 Votre code de sécurité - Cimetière",
        html_content=f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1A56DB;">Double authentification requise</h2>
            <p>Bonjour <b>{user.username}</b>,</p>
            <p>Voici votre code de validation à usage unique pour accéder à votre espace :</p>
            <div style="background: #F3F4F6; padding: 15px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 5px; color: #1A56DB; border-radius: 8px; margin: 20px 0;">
                {code}
            </div>
            <p style="font-size: 12px; color: #6B7280;">Ce code expirera automatiquement dans 10 minutes.</p>
        </div>
        """
    )

    if not email_sent:
        print("🔴 Erreur lors de l'envoi du code MFA")
        return {"success": False, "message": "Erreur lors de l'envoi du code de sécurité."}

    print(f"✅ Email MFA envoyé à {user.email}")
    print("🔵 ===== FIN LOGIN =====")

    return {
        "success": True,
        "mfa_required": True,
        "message": "Un code de validation a été envoyé par email."
    }


@router.post("/verify-mfa")
def verify_mfa_code(request, data: MFAVerifyRequestSchema) -> Dict[str, Any]:
    """Vérification du code MFA."""
    
    print("🔵 ===== VERIFY MFA =====")
    print(f"🔵 Email: {data.email}")
    print(f"🔵 Code: {data.code}")
    
    try:
        user = User.objects.get(email=data.email)
        print(f"🔵 Utilisateur trouvé: {user.email}")
    except User.DoesNotExist:
        print("🔴 Utilisateur introuvable")
        return {"success": False, "message": "Utilisateur introuvable"}
    
    mfa = MFACode.objects.filter(
        user=user,
        code=data.code,
        is_used=False
    ).last()
    
    if not mfa:
        print("🔴 Code MFA non trouvé")
        return {"success": False, "message": "Code invalide"}
    
    if not mfa.is_valid():
        print("🔴 Code MFA expiré")
        return {"success": False, "message": "Code expiré"}
    
    print(f"✅ Code MFA valide pour {user.email}")
    
    mfa.is_used = True
    mfa.save()
    print("🔵 Code MFA marqué comme utilisé")
    
    refresh = RefreshToken.for_user(user)
    print(f"✅ Token généré pour {user.email}")
    print("🔵 ===== FIN VERIFY MFA =====")
    
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
    print(f"🔵 GET /me - Utilisateur: {user.email}")
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
    print(f"🔵 PATCH /me - Utilisateur: {user.email}")
    
    if user.last_profile_update:
        elapsed = timezone.now() - user.last_profile_update
        if elapsed < timedelta(hours=48):
            remaining_hours = 48 - int(elapsed.total_seconds() // 3600)
            print(f"🔴 Délai d'attente: {remaining_hours}h restantes")
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
            print(f"🔵 Changement: {key} -> '{value}'")
    
    if not changes:
        print("🔴 Aucun changement détecté")
        return {"success": False, "message": "Aucune modification détectée"}
    
    user.last_profile_update = timezone.now()
    user.save()
    print(f"✅ Profil mis à jour pour {user.email}")
    
    admins = User.objects.filter(role="ADMIN").values_list("email", flat=True)
    
    if admins:
        print(f"🔵 Notification envoyée aux admins: {list(admins)}")
        send_brevo_email(
            to_email=list(admins)[0],
            subject="Modification de profil utilisateur",
            html_content=f"""
            <h2>Modification de profil</h2>
            <p>L'utilisateur <strong>{user.username}</strong> ({user.email}) a modifié son profil :</p>
            <ul>
                {''.join([f'<li>{change}</li>' for change in changes])}
            </ul>
            """
        )
    
    return {"success": True, "message": "Profil mis à jour"}


@router.post("/logout", auth=auth)
def logout_user(request, data: LogoutRequestSchema) -> Dict[str, Any]:
    """Déconnexion de l'utilisateur."""
    user = request.auth
    print(f"🔵 LOGOUT - Utilisateur: {user.email}")
    try:
        token = RefreshToken(data.refresh)
        token.blacklist()
        print("✅ Token blacklisté")
        return {"success": True, "message": "Déconnecté"}
    except TokenError as e:
        print(f"🔴 Erreur: {e}")
        return {"success": False, "message": "Token invalide ou déjà expiré"}


@router.get("/", auth=auth)
def list_users(request) -> Dict[str, Any]:
    """Récupère la liste de tous les utilisateurs (admin uniquement)."""
    user = request.auth
    
    print("🔵 ===== LISTE UTILISATEURS =====")
    print(f"🔵 Utilisateur connecté: {user.email}")
    print(f"🔵 Rôle: {user.role}")
    
    if user.role != "ADMIN":
        print("🔴 Accès refusé - rôle insuffisant")
        return {"success": False, "message": "Accès refusé"}
    
    try:
        users = list(User.objects.all().values(
            "id", "username", "email", "role", "telephone", "is_active", "mfa_active"
        ))
        print(f"🔵 Utilisateurs trouvés: {len(users)}")
        for u in users:
            print(f"🔵 - {u['email']} ({u['role']}) - Actif: {u['is_active']}")
        print("🔵 ===== FIN LISTE UTILISATEURS =====")
        return {"success": True, "users": users}
    except Exception as e:
        print(f"🔴 Erreur: {e}")
        return {"success": False, "message": str(e)}


@router.patch("/{user_id}/role", auth=auth)
def update_user_role(request, user_id: int, role: str) -> Dict[str, Any]:
    """Met à jour le rôle d'un utilisateur."""
    user = request.auth
    print(f"🔵 UPDATE ROLE - Admin: {user.email}, Target ID: {user_id}, New Role: {role}")
    
    if user.role != "ADMIN":
        print("🔴 Accès refusé")
        return {"success": False, "message": "Accès refusé"}

    try:
        target = User.objects.get(id=user_id)
        print(f"🔵 Cible trouvée: {target.email} (ancien rôle: {target.role})")
    except User.DoesNotExist:
        print(f"🔴 Utilisateur {user_id} introuvable")
        return {"success": False, "message": "Utilisateur introuvable"}

    valid_roles = ["ADMIN", "AGENT", "SECRETARIAT", "CLIENT"]
    if role not in valid_roles:
        print(f"🔴 Rôle invalide: {role}")
        return {"success": False, "message": "Rôle invalide"}

    target.role = role
    target.save()
    print(f"✅ Rôle mis à jour pour {target.email} -> {role}")

    return {"success": True, "message": "Rôle mis à jour"}


@router.patch("/{user_id}/toggle-active", auth=auth)
def toggle_user_active(request, user_id: int) -> Dict[str, Any]:
    """Active/désactive un utilisateur."""
    user = request.auth
    print(f"🔵 TOGGLE ACTIVE - Admin: {user.email}, Target ID: {user_id}")
    
    if user.role != "ADMIN":
        print("🔴 Accès refusé")
        return {"success": False, "message": "Accès refusé"}

    try:
        target = User.objects.get(id=user_id)
        print(f"🔵 Cible trouvée: {target.email} (actif: {target.is_active})")
    except User.DoesNotExist:
        print(f"🔴 Utilisateur {user_id} introuvable")
        return {"success": False, "message": "Utilisateur introuvable"}

    if target.id == user.id:
        print("🔴 Tentative de désactivation de son propre compte")
        return {"success": False, "message": "Vous ne pouvez pas désactiver votre propre compte"}

    target.is_active = not target.is_active
    target.save()
    print(f"✅ Statut mis à jour pour {target.email} -> actif: {target.is_active}")

    return {"success": True, "message": "Statut mis à jour", "is_active": target.is_active}


@router.get("/pending-pick", auth=auth)
def get_pending_location_pick(request) -> Dict[str, Any]:
    """Récupère et efface les coordonnées en attente."""
    user = request.auth
    
    print(f"🔵 GET PENDING PICK - Utilisateur: {user.email}")
    
    if user.pending_pick_lat is None:
        print("🔴 Aucune coordonnée en attente")
        return {"has_pick": False}
    
    data = {
        "has_pick": True,
        "latitude": user.pending_pick_lat,
        "longitude": user.pending_pick_lng,
        "caveau_id": user.pending_pick_caveau_id,
    }
    
    print(f"🔵 Coordonnées récupérées: lat={user.pending_pick_lat}, lng={user.pending_pick_lng}")
    
    user.pending_pick_lat = None
    user.pending_pick_lng = None
    user.pending_pick_caveau_id = None
    user.save()
    print("🔵 Coordonnées effacées")
    
    return data