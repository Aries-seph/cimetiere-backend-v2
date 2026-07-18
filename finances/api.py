# finances/api.py
from ninja import Router
from finances.models import Paiement
from finances.schemas import PaiementCreateSchema, PaiementResponseSchema
from reservations.models import Reservation
from users.auth import JWTAuth
import uuid
from django.core.mail import EmailMessage
from finances.pdf import generate_invoice_pdf
from typing import List, Dict, Any
from django.db.models import Q
import logging
import threading

logger = logging.getLogger(__name__)

router = Router()
auth = JWTAuth()


def _is_admin(user) -> bool:
    """Vérifie si l'utilisateur a un rôle administratif."""
    return user.role in ["ADMIN", "SECRETARIAT"]


def _generate_reference() -> str:
    """Génère une référence unique pour un paiement."""
    return f"PAY-{uuid.uuid4().hex[:8].upper()}"


def _send_invoice_email(paiement: Paiement):
    """Envoie la facture par email avec gestion robuste des erreurs."""
    try:
        # Forcer le rafraîchissement depuis la BDD avec les relations nécessaires
        paiement_complet = Paiement.objects.select_related(
            'client', 
            'reservation', 
            'reservation__caveau'
        ).get(id=paiement.id)
        
        pdf_buffer = generate_invoice_pdf(paiement_complet)
        
        email = EmailMessage(
            subject='Votre facture de paiement',
            body=f'Bonjour {paiement_complet.client.username},\n\nVeuillez trouver ci-joint votre facture pour le paiement {paiement_complet.reference}.\n\nMerci.',
            from_email='jeremykounkou@icloud.com',
            to=[paiement_complet.client.email],
        )
        
        email.attach(
            f'facture_{paiement_complet.reference}.pdf',
            pdf_buffer.read(),
            'application/pdf'
        )
        email.send()
        logger.info(f"Email de facture envoyé avec succès pour le paiement {paiement_complet.reference}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de facture pour le paiement {paiement.id}: {str(e)}")
        # Optionnel: lever l'exception ou la laisser silencieuse pour ne pas bloquer la réponse API
        raise e


@router.post("/", auth=auth)
def create_new_paiement(request, data: PaiementCreateSchema):
    """Crée un nouveau paiement."""
    user = request.auth

    try:
        reservation = Reservation.objects.get(id=data.reservation_id)
    except Reservation.DoesNotExist:
        return {"success": False, "message": "Réservation introuvable"}

    if reservation.client != user and not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    reference = _generate_reference()

    paiement = Paiement.objects.create(
        reservation=reservation,
        client=user,
        montant=data.montant,
        canal=data.canal,
        reference=reference
    )

    return {
        "success": True,
        "message": "Paiement enregistré",
        "reference": paiement.reference,
        "statut": paiement.statut
    }


@router.get("/mes-paiements", auth=auth, response=List[Dict[str, Any]])
def get_my_paiements(request):
    """Récupère les paiements de l'utilisateur connecté."""
    user = request.auth
    return list(Paiement.objects.filter(client=user).values())


@router.get("/admin", auth=auth, response=List[Dict[str, Any]])
def get_all_paiements_admin(request):
    """Récupère tous les paiements (admin uniquement)."""
    user = request.auth
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}
    
    sort_by = request.GET.get('sort', '-created_at')
    allowed_sort_fields = ['created_at', '-created_at', 'montant', '-montant', 'statut', '-statut']
    
    if sort_by not in allowed_sort_fields:
        sort_by = '-created_at'
    
    return list(Paiement.objects.all().order_by(sort_by).values())



@router.post("/validate/{paiement_id}", auth=auth)
def validate_paiement_request(request, paiement_id: int):
    """Valide un paiement."""
    user = request.auth
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    try:
        paiement = Paiement.objects.get(id=paiement_id)
    except Paiement.DoesNotExist:
        return {"success": False, "message": "Paiement introuvable"}

    paiement.statut = "VALIDE"
    paiement.save()

    try:
        _send_invoice_email(paiement)
        return {"success": True, "message": "Paiement validé et facture envoyée"}
    except Exception as mail_err:
        return {
            "success": True, 
            "message": f"Paiement validé, mais la facture n'a pas pu être envoyée par mail : {str(mail_err)}"
        }


@router.post("/reject/{paiement_id}", auth=auth)
def reject_paiement_request(request, paiement_id: int):
    """Refuse un paiement."""
    user = request.auth
    if not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    try:
        paiement = Paiement.objects.get(id=paiement_id)
    except Paiement.DoesNotExist:
        return {"success": False, "message": "Paiement introuvable"}

    paiement.statut = "REFUSE"
    paiement.save()

    return {"success": True, "message": "Paiement refusé"}


@router.get("/historique/{reservation_id}", auth=auth)
def get_paiement_history(request, reservation_id: int):
    """Récupère l'historique des paiements d'une réservation."""
    user = request.auth

    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return {"success": False, "message": "Réservation introuvable"}

    if reservation.client != user and not _is_admin(user):
        return {"success": False, "message": "Accès refusé"}

    paiements = Paiement.objects.filter(reservation_id=reservation_id).values()
    total_paid = sum(p["montant"] for p in paiements)

    return {
        "paiements": list(paiements),
        "total_paye": float(total_paid)
    }