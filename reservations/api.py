# reservations/api.py
from ninja import Router
from reservations.models import Reservation, AuditLog
from caveaux.models import Caveau
from reservations.schemas import ReservationCreateSchema, ReservationResponseSchema
from users.auth import JWTAuth
from django.core.mail import send_mail
from typing import List, Dict, Any

router = Router()
auth = JWTAuth()


def _is_admin(user) -> bool:
    """Vérifie si l'utilisateur a un rôle administratif."""
    return user.role in ["ADMIN", "SECRETARIAT"]


def _notify_admins(subject: str, message: str):
    """Envoie une notification aux administrateurs."""
    send_mail(
        subject=subject,
        message=message,
        from_email='jeremykounkou@gicloud.com',
        recipient_list=['jeremykounkou@gicloud.com'],
    )


def _notify_user(email: str, subject: str, message: str):
    """Envoie une notification à un utilisateur."""
    send_mail(
        subject=subject,
        message=message,
        from_email='jeremykounkou@gicloud.com',
        recipient_list=[email],
    )


@router.post("/", auth=auth)
def create_new_reservation(request, data: ReservationCreateSchema):
    """Crée une nouvelle réservation."""
    user = request.auth
    
    try:
        caveau = Caveau.objects.get(id=data.caveau_id)
    except Caveau.DoesNotExist:
        return {"success": False, "message": "Caveau introuvable"}
    
    if caveau.statut != "DISPONIBLE":
        return {"success": False, "message": "Caveau non disponible"}
    
    existing = Reservation.objects.filter(
        caveau=caveau,
        statut="EN_ATTENTE"
    ).first()
    
    if existing:
        return {"success": False, "message": "Caveau déjà en cours de réservation"}
    
    reservation = Reservation.objects.create(
        client=user,
        caveau=caveau,
        nom_defunt=data.nom_defunt,
        date_deces=data.date_deces,
        commentaire=data.commentaire or ""
    )
    
    caveau.statut = "RESERVE"
    caveau.save()
    
    AuditLog.objects.create(
        user=user,
        reservation=reservation,
        action="CREATION",
        detail=f"Réservation créée pour le caveau {caveau.reference}"
    )
    
    _notify_admins(
        subject='Nouvelle réservation en attente',
        message=f'Une nouvelle réservation a été soumise par {user.email} pour le caveau {caveau.reference}.'
    )
    
    return {
        "success": True,
        "message": "Réservation créée",
        "reservation_id": reservation.id
    }


@router.get("/mes-reservations", auth=auth, response=List[Dict[str, Any]])
def get_my_reservations(request):
    """Récupère les réservations de l'utilisateur connecté."""
    user = request.auth
    return list(
        Reservation.objects.filter(client=user).values()
    )


@router.get("/admin", auth=auth, response=List[Dict[str, Any]])
def get_all_reservations_admin(request):
    """Récupère toutes les réservations (admin uniquement)."""
    user = request.auth
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    return list(Reservation.objects.all().values())


@router.get("/{reservation_id}", auth=auth, response=Dict[str, Any])
def get_reservation_detail(request, reservation_id: int):
    """Récupère les détails d'une réservation."""
    user = request.auth
    
    if _is_admin(user):
        reservation = Reservation.objects.filter(id=reservation_id).values().first()
    else:
        reservation = Reservation.objects.filter(
            id=reservation_id,
            client=user
        ).values().first()
    
    if not reservation:
        return {"success": False, "message": "Réservation introuvable"}
    
    return reservation


@router.post("/validate/{reservation_id}", auth=auth)
def validate_reservation_request(request, reservation_id: int):
    """Valide une réservation."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return {"success": False, "message": "Réservation introuvable"}
    
    reservation.statut = "VALIDEE"
    reservation.save()
    
    caveau = reservation.caveau
    caveau.statut = "OCCUPE"
    caveau.save()
    
    AuditLog.objects.create(
        user=user,
        reservation=reservation,
        action="VALIDATION",
        detail=f"Réservation validée par {user.email}"
    )
    
    _notify_user(
        email=reservation.client.email,
        subject='Réservation validée',
        message=f'Bonjour {reservation.client.username},\n\nVotre réservation pour le caveau {caveau.reference} a été validée.\n\nMerci.'
    )
    
    return {"success": True, "message": "Réservation validée"}


@router.post("/reject/{reservation_id}", auth=auth)
def reject_reservation_request(request, reservation_id: int):
    """Refuse une réservation."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return {"success": False, "message": "Réservation introuvable"}
    
    reservation.statut = "REFUSEE"
    reservation.save()
    
    caveau = reservation.caveau
    caveau.statut = "DISPONIBLE"
    caveau.save()
    
    AuditLog.objects.create(
        user=user,
        reservation=reservation,
        action="REFUS",
        detail=f"Réservation refusée par {user.email}"
    )
    
    _notify_user(
        email=reservation.client.email,
        subject='Réservation refusée',
        message=f'Bonjour {reservation.client.username},\n\nVotre réservation pour le caveau {caveau.reference} a été refusée.\n\nPour plus d\'informations, contactez l\'administration.'
    )
    
    return {"success": True, "message": "Réservation refusée"}


@router.get("/audit/{reservation_id}", auth=auth, response=List[Dict[str, Any]])
def get_reservation_audit_logs(request, reservation_id: int):
    """Récupère l'historique d'une réservation."""
    user = request.auth
    
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    return list(
        AuditLog.objects.filter(
            reservation_id=reservation_id
        ).values(
            "user__email",
            "action",
            "detail",
            "created_at"
        )
    )